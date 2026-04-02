import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Home,
  Activity,
  History,
  User,
  Stethoscope,
  LogOut,
  Menu,
  X
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const Sidebar = ({ open, onClose, currentPath }) => {
  const { user, logout } = useAuth()

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: Home,
      current: currentPath === '/dashboard'
    },
    {
      name: 'AI Diagnosis',
      href: '/diagnosis',
      icon: Stethoscope,
      current: currentPath.includes('/diagnosis')
    },
    {
      name: 'History',
      href: '/history',
      icon: History,
      current: currentPath.includes('/history')
    },
    {
      name: 'Profile',
      href: '/profile',
      icon: User,
      current: currentPath.includes('/profile')
    }
  ]

  const handleLogout = () => {
    logout()
    onClose()
  }

  return (
    <>
      {/* Mobile sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-xl transform transition-transform duration-300 ease-in-out lg:hidden ${
        open ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <Stethoscope className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">MediAI</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <nav className="mt-6 px-3">
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                <item.icon className="mr-3 h-5 w-5" />
                {item.name}
              </NavLink>
            ))}
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="px-3 py-2">
              <p className="text-sm font-medium text-gray-900">User</p>
              <p className="text-sm text-gray-500 truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-red-50 hover:text-red-700 transition-colors"
            >
              <LogOut className="mr-3 h-5 w-5" />
              Logout
            </button>
          </div>
        </nav>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0">
        <div className="flex flex-col flex-grow bg-white border-r border-gray-200 pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-6">
            <Stethoscope className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">MediAI</span>
          </div>

          <nav className="mt-8 flex-1 px-4">
            <div className="space-y-1">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`
                  }
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  {item.name}
                </NavLink>
              ))}
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
              <div className="px-3 py-2">
                <p className="text-sm font-medium text-gray-900">User</p>
                <p className="text-sm text-gray-500 truncate">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center w-full px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-red-50 hover:text-red-700 transition-colors"
              >
                <LogOut className="mr-3 h-5 w-5" />
                Logout
              </button>
            </div>
          </nav>
        </div>
      </div>
    </>
  )
}

export default Sidebar
