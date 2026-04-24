import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  PhotoIcon,
  InformationCircleIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/solid'
import {
  HomeIcon as HomeOutline,
  PhotoIcon as PhotoOutline,
  InformationCircleIcon as InformationCircleOutline,
  EnvelopeIcon as EnvelopeOutline,
} from '@heroicons/react/24/outline'

const tabs = [
  { to: '/', label: 'Home', end: true, Active: HomeIcon, Idle: HomeOutline },
  { to: '/detect', label: 'Analyze', Active: PhotoIcon, Idle: PhotoOutline },
  {
    to: '/about',
    label: 'About',
    end: false,
    Active: InformationCircleIcon,
    Idle: InformationCircleOutline,
  },
  { to: '/contact', label: 'Contact', Active: EnvelopeIcon, Idle: EnvelopeOutline },
]

export default function MobileBottomNav() {
  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-[100] border-t border-black/10 bg-white/95 shadow-[0_-4px_24px_rgba(0,0,0,0.06)] backdrop-blur-md"
      style={{
        paddingBottom: 'max(0.5rem, env(safe-area-inset-bottom, 0px))',
        paddingTop: '0.5rem',
        paddingLeft: 'max(0.5rem, env(safe-area-inset-left, 0px))',
        paddingRight: 'max(0.5rem, env(safe-area-inset-right, 0px))',
      }}
      aria-label="Main navigation"
    >
      <div className="mx-auto flex max-w-lg items-stretch justify-around">
        {tabs.map(({ to, label, end, Active, Idle }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex min-w-0 flex-1 flex-col items-center gap-0.5 py-1 text-[11px] font-semibold leading-tight transition-colors ${
                isActive
                  ? 'text-primary'
                  : 'text-tertiary active:text-primary/80'
              }`
            }
          >
            {({ isActive }) => {
              const I = isActive ? Active : Idle
              return (
                <>
                  <I className="h-6 w-6 shrink-0" aria-hidden />
                  <span className="truncate px-0.5">{label}</span>
                </>
              )
            }}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
