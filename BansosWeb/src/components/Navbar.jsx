import { Link } from 'react-router-dom'
import logoDesa from '../assets/logo desa.png'

function Navbar() {
  return (
    <header className="site-navbar">
      <Link className="brand" to="/">
        <div className="brand-logo">
          <img src={logoDesa} alt="Logo Desa Citorek Timur" />
        </div>
        <div>
          <strong>Desa Citorek Timur</strong>
          <span>Lebak, Banten</span>
        </div>
      </Link>
      <Link className="btn btn-primary" to="/login">
        Login Admin
      </Link>
    </header>
  )
}

export default Navbar
