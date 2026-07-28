import { useEffect } from 'react'
import Chatbot from '../components/Chatbot'
import Navbar from '../components/Navbar'
import citorekImage from '../assets/ctrk.jpeg'

function LandingPage() {
  useEffect(() => {
    document.documentElement.classList.remove('dark-theme')
  }, [])

  return (
    <div className="landing-page">
      <div className="public-frame">
        <Navbar />
        <main className="public-main">
          <section className="public-intro" aria-labelledby="public-title">
            <div>
              <h1 id="public-title">Sistem Penentuan Kelayakan Penerima Bantuan Sosial</h1>
              <p className="public-location">
                Desa Citorek Timur, Kecamatan Cibeber, Kabupaten Lebak, Provinsi Banten
              </p>
            </div>

            <div className="village-illustration">
              <img src={citorekImage} alt="Pemandangan Desa Citorek Timur" />
            </div>

            <p className="public-description">
              Sistem ini digunakan untuk membantu proses penentuan kelayakan warga
              penerima bantuan sosial secara objektif dan tepat sasaran.
            </p>
          </section>

          <div className="public-chat-panel">
            <Chatbot />
          </div>
        </main>
      </div>
    </div>
  )
}

export default LandingPage
