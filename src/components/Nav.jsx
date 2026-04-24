import logo from '../assets/Logo.svg'
import { Link, NavLink } from 'react-router-dom'

const Nav = () => {
  const navLinkStyle = ({ isActive }) => ({
    color: isActive ? 'black' : '#767676',
  })

  return (
    <>
      {/* Mobile: native-style top bar */}
      <header
        className="lg:hidden sticky top-0 z-50 flex w-full max-w-full items-center justify-center gap-2 border-b border-black/5 bg-white/95 py-3 pl-[max(1rem,env(safe-area-inset-left,0px))] pr-[max(1rem,env(safe-area-inset-right,0px))] pt-[max(0.5rem,env(safe-area-inset-top,0px))] backdrop-blur-sm"
        style={{ minHeight: '3.5rem' }}
      >
        <Link to="/" className="flex min-w-0 items-center gap-2">
          <img src={logo} alt="Tomato Planet" className="h-8 w-auto shrink-0" />
          <span className="truncate text-base font-bold tracking-tight text-quaternary">
            Tomato Planet
          </span>
        </Link>
      </header>

      {/* Desktop */}
      <div className="hidden w-full max-w-[100vw] items-center justify-between overflow-x-hidden px-5 py-4 lg:flex lg:px-[120px] lg:py-7">
        <Link to="/" className="shrink-0">
          <img
            src={logo}
            alt="Tomato Planet"
            className="h-11 w-auto"
          />
        </Link>

        <div className="flex items-center justify-end gap-14 text-lg">
          <NavLink to="/" style={navLinkStyle} end>
            Home
          </NavLink>
          <NavLink to="/detect" style={navLinkStyle}>
            Analyze
          </NavLink>
          <NavLink to="/about" style={navLinkStyle}>
            About Us
          </NavLink>
          <NavLink to="/contact" style={navLinkStyle}>
            Contact Us
          </NavLink>
        </div>
      </div>
    </>
  )
}

export default Nav
