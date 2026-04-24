import { Link } from 'react-router-dom'
import logo from '../assets/Logo.svg'

const Footer = () => {
  return (
    <footer>
      <div className="hidden items-start justify-between gap-10 border-t border-black/5 py-16 text-lg lg:flex lg:px-[120px] lg:py-36">
        <Link
          to="/"
          className="flex w-1/2 items-center justify-center lg:block"
        >
          <img src={logo} alt="Tomato Planet" />
        </Link>
        <div className="flex w-1/2 flex-col items-start justify-start gap-10 lg:flex-row lg:gap-20">
          <div>
            <h2 className="pb-8 text-lg font-semibold text-primary lg:pb-14">Team</h2>
            <ul className="flex flex-col gap-4 text-left lg:gap-8">
              <li>Gardening</li>
              <li>Edible</li>
            </ul>
          </div>
          <div>
            <h2 className="pb-8 text-lg font-semibold text-primary lg:pb-14">Services</h2>
            <ul className="flex flex-col gap-4 text-left lg:gap-8">
              <li>Project</li>
              <li>Affiliate</li>
            </ul>
          </div>
          <div>
            <h2 className="pb-8 text-lg font-semibold text-primary lg:pb-14">Terms of use</h2>
            <ul className="flex flex-col gap-4 text-left lg:gap-8">
              <li>Privacy Policy</li>
              <li>Contact us</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Mobile: light strip above bottom tab bar */}
      <div className="mt-2 border-t border-black/5 px-5 py-6 text-center text-sm text-tertiary lg:hidden">
        <p>© {new Date().getFullYear()} Tomato Planet. Grow with confidence.</p>
      </div>
    </footer>
  )
}

export default Footer
