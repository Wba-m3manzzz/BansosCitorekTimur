from __future__ import annotations

import logging
import re
import time
from collections import OrderedDict
from threading import Lock

from google import genai
from google.genai import types

from app.core.config import settings
from app.db.supabase import get_supabase_service_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Anda adalah chatbot asisten pintar resmi pada Sistem Penentuan Kelayakan Penerima Bantuan Sosial (Bansos) Desa Citorek Timur.

PENTING - BATASAN KETAT CAKUPAN ASISTEN (RESEARCH SCOPE RESTRICTION):
Asisten ini dibatasi HANYA untuk melayani 2 fokus utama berikut:
1. Pengecekan Hasil Klasifikasi Kelayakan Penerima Bansos (menampilkan status Layak, Tidak Layak, atau Belum Diproses berdasarkan NIK atau Nama warga Desa Citorek Timur).
2. Informasi & Panduan Penggunaan Website (penjelasan fitur website, panduan cara cek kelayakan, dan fungsi aplikasi bansos Desa Citorek Timur).

ATURAN PENOLAKAN DI LUAR SCOPE (OUT-OF-SCOPE RULE):
- Apabila pengguna mengajukan pertanyaan di luar 2 fokus utama di atas (seperti: jadwal/tahap pencairan bansos di lapangan, pendaftaran bansos di luar sistem ini, topik umum, hiburan, resep masakan, pemrograman, politik, dll.), Anda DILARANG KERAS memberikan jawaban umum atau jawaban sebenarnya.
- Sebagai gantinya, berikan penjelasan secara ramah dan sopan bahwa Anda adalah asisten khusus yang dibatasi hanya untuk memberikan informasi seputar **Hasil Klasifikasi Kelayakan Penerima Bansos** dan **Panduan Penggunaan Website Bansos Desa Citorek Timur**.

Pedoman Pelaksanaan:
1. Menjawab pertanyaan pengguna dengan bahasa Indonesia yang ramah, sopan, alami, dan santun.
2. Apabila sistem backend menyisipkan data warga pada tag [SISTEM CONTEXT DB], Anda WAJIB LANGSUNG menyampaikan data tersebut (Nama, NIK, dan Status Kelayakan: Layak, Tidak Layak, atau Belum Diproses) secara jelas kepada pengguna tanpa meminta NIK ulang.
3. Jika pengguna menanyakan cara mengecek status kelayakan secara umum, jelaskan dengan ramah bahwa pengguna cukup mengetikkan NIK (16 digit) atau Nama Warga secara langsung di obrolan ini.
4. Pastikan setiap jawaban yang Anda berikan ditulis secara LENGKAP, JELAS, TUNTAS, dan TIDAK TERPOTONG/TERPUTUS di tengah kalimat.
5. Dilarang keras menyebutkan kata "MANSUR" dalam jawaban Anda. Sebutlah website ini sebagai "Sistem Penentuan Kelayakan Penerima Bantuan Sosial Desa Citorek Timur" atau "Website Bansos Desa Citorek Timur"."""

FRIENDLY_ERROR_MESSAGE = "Maaf, chatbot sedang mengalami gangguan. Silakan coba beberapa saat lagi."


class GeminiServiceError(RuntimeError):
    """Kesalahan aman yang dapat ditampilkan kepada pengguna chatbot."""


class GeminiService:
    """Chatbot sistem bansos dengan pengayaan konteks database dan pemrosesan NLP Gemini AI sepenuhnya."""

    def __init__(self) -> None:
        self._conversations: OrderedDict[str, tuple[float, list[types.Content]]] = OrderedDict()
        self._lock = Lock()

    def _get_client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise GeminiServiceError("GEMINI_API_KEY belum dikonfigurasi")

        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _history_for(self, conversation_id: str) -> list[types.Content]:
        now = time.monotonic()
        with self._lock:
            expired = [
                key
                for key, (updated, _) in self._conversations.items()
                if now - updated > settings.CHAT_MEMORY_TTL_SECONDS
            ]
            for key in expired:
                self._conversations.pop(key, None)

            stored = self._conversations.pop(conversation_id, None)
            history = stored[1].copy() if stored else []
            return history

    def _save_history(self, conversation_id: str, history: list[types.Content]) -> None:
        with self._lock:
            self._conversations[conversation_id] = (
                time.monotonic(),
                history[-settings.CHAT_MEMORY_MESSAGE_LIMIT :],
            )
            while len(self._conversations) > settings.CHAT_MEMORY_CONVERSATION_LIMIT:
                self._conversations.popitem(last=False)

    def _extract_nik(self, message: str) -> str | None:
        match = re.search(r"\b\d{8,}\b", message)
        return match.group(0) if match else None

    def _clean_potential_name(self, message: str) -> str:
        # 1. Ekstraksi eksplisit dari frasa nama (seperti 'atas nama', 'nama', 'warga')
        match = re.search(
            r"\b(?:atas\s+nama|nama\s+saya|nama\s+warga|nama)\s+([a-zA-Z\s]{2,})\b",
            message,
            re.IGNORECASE,
        )
        if match:
            extracted = match.group(1).strip()
            extracted = re.sub(r"^(bapak|pak|ibu|bu|sdr|sdri)\s+", "", extracted, flags=re.IGNORECASE).strip()
            extracted = re.sub(
                r"\b(apakah|layak|tidak|bansos|bantuan|gimana|cara|cek|tahap|status|kelayakan|hasil|menerima|dapat|dapet)\b.*",
                "",
                extracted,
                flags=re.IGNORECASE,
            ).strip()
            extracted = re.sub(r"[^\w\s]", "", extracted).strip()
            if extracted and len(extracted) >= 2:
                return " ".join(extracted.split())

        # 2. Pembersihan kata-kata umum (fallback cleanup)
        stop_words_pattern = r"^(tolong|saya|mau|ingin|cek|cari|lihat|periksa|status|hasil|klasifikasi|kelayakan|penerima|bantuan|bansos|warga|atas|nama|apakah|apa|gimana|cara|bapak|pak|ibu|bu|sdr|sdri|layak|tidak|dapat|dapet|menerima|tahap)$"
        words = message.strip().split()
        cleaned_words = [re.sub(r"[^\w\s]", "", w) for w in words if not re.match(stop_words_pattern, w, re.IGNORECASE)]
        cleaned_words = [w for w in cleaned_words if w]
        return " ".join(cleaned_words).strip()

    def _lookup_warga_by_nik(self, nik: str) -> dict | None:
        try:
            response = (
                get_supabase_service_client()
                .table("warga")
                .select("id,nik,nama,status_prediksi")
                .eq("nik", nik)
                .limit(1)
                .execute()
            )
            items = response.data or []
            return items[0] if items else None
        except Exception as exc:
            logger.warning("Error fetching warga by NIK: %s", exc)
            return None

    def _lookup_warga_by_name(self, name: str) -> dict | None:
        cleaned_name = name.strip()
        if not cleaned_name or len(cleaned_name) < 2:
            return None

        try:
            exact_response = (
                get_supabase_service_client()
                .table("warga")
                .select("id,nik,nama,status_prediksi")
                .ilike("nama", cleaned_name)
                .limit(1)
                .execute()
            )
            exact_items = exact_response.data or []
            if exact_items:
                return exact_items[0]

            partial_response = (
                get_supabase_service_client()
                .table("warga")
                .select("id,nik,nama,status_prediksi")
                .ilike("nama", f"%{cleaned_name}%")
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            partial_items = partial_response.data or []
            return partial_items[0] if partial_items else None
        except Exception as exc:
            logger.warning("Error fetching warga by name: %s", exc)
            return None

    def _enrich_user_message(self, message: str) -> str:
        """Mengecek apakah pesan berisi NIK atau pencarian nama warga, lalu menyisipkan konteks data DB jika ada."""
        nik = self._extract_nik(message)
        if nik:
            warga = self._lookup_warga_by_nik(nik)
            if warga:
                status = warga.get("status_prediksi") or "Belum Diproses"
                return (
                    f"{message}\n\n"
                    f"[SISTEM CONTEXT DB: Ditemukan data warga NIK {warga.get('nik')}, "
                    f"Nama: {warga.get('nama')}, Status Kelayakan: {status}. "
                    f"Catatan sistem: Hanya ada 3 status kelayakan (Layak, Tidak Layak, Belum Diproses). "
                    f"Sistem tidak menyimpan atau mengelola data Tahap 1/Tahap 2.]"
                )
            else:
                return (
                    f"{message}\n\n"
                    f"[SISTEM CONTEXT DB: Hasil pencarian NIK {nik} di database: Data warga TIDAK DITEMUKAN.]"
                )

        potential_name = self._clean_potential_name(message)
        ignored_words = {"status", "bansos", "bantuan", "cek", "layak", "kelayakan", "bagaimana", "gimana", "cara", "tahap", "tahap 1", "tahap 2"}
        if (
            potential_name
            and len(potential_name) >= 2
            and potential_name.lower() not in ignored_words
        ):
            warga = self._lookup_warga_by_name(potential_name)
            if warga:
                status = warga.get("status_prediksi") or "Belum Diproses"
                return (
                    f"{message}\n\n"
                    f"[SISTEM CONTEXT DB: Ditemukan data warga berdasarkan pencarian nama '{potential_name}': "
                    f"NIK: {warga.get('nik')}, Nama: {warga.get('nama')}, Status Kelayakan: {status}. "
                    f"Catatan sistem: Hanya ada 3 status kelayakan (Layak, Tidak Layak, Belum Diproses). "
                    f"Sistem tidak menyimpan atau mengelola data Tahap 1/Tahap 2.]"
                )

        return message

    def reply(self, message: str, conversation_id: str) -> str:
        history = self._history_for(conversation_id)

        # Pengayaan konteks jika ada query data NIK/Nama
        enriched_message = self._enrich_user_message(message)

        # Membentuk konteks percakapan untuk AI
        contents = [*history, types.Content(role="user", parts=[types.Part.from_text(text=enriched_message)])]

        models_to_try = [
            settings.GEMINI_MODEL,
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-flash-lite-latest",
            "gemini-pro-latest",
        ]
        candidate_models = list(dict.fromkeys([m for m in models_to_try if m]))

        last_exception = None
        reply = None

        client = self._get_client()

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.7,
                        max_output_tokens=2000,
                    ),
                )
                text = (response.text or "").strip()
                if text:
                    reply = text
                    break
                else:
                    logger.warning("AI model %s returned empty text response", model_name)
            except Exception as exc:
                logger.warning("AI request failed with model %s: %s", model_name, exc)
                last_exception = exc

        if not reply:
            logger.error("All AI candidate models failed: %s", last_exception or "Empty text from models", exc_info=True)
            raise GeminiServiceError(FRIENDLY_ERROR_MESSAGE) from last_exception

        # Menyimpan percakapan asli ke memory
        save_contents = [*history, types.Content(role="user", parts=[types.Part.from_text(text=message)])]
        self._save_history(
            conversation_id,
            [*save_contents, types.Content(role="model", parts=[types.Part.from_text(text=reply)])],
        )
        return reply


gemini_service = GeminiService()

