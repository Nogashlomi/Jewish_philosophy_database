import { useState } from 'react'
import { LogIn, LogOut } from 'lucide-react'
import type { User } from 'firebase/auth'
import { useAuth } from '../auth/authContext'

function initials(user: User): string {
  const source = user.displayName || user.email || '?'
  const words = source.split(/[\s@._-]+/).filter(Boolean)
  return (words.length > 1 ? words[0][0] + words[1][0] : source.slice(0, 2)).toUpperCase()
}

function Avatar({ user }: { user: User }) {
  const [imageFailed, setImageFailed] = useState(false)
  const label = user.displayName || user.email || 'Signed in'

  if (user.photoURL && !imageFailed) {
    return (
      <img
        src={user.photoURL}
        alt={label}
        title={label}
        referrerPolicy="no-referrer"
        onError={() => setImageFailed(true)}
        className="h-8 w-8 rounded-full object-cover"
      />
    )
  }

  return (
    <span
      title={label}
      aria-label={label}
      className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white"
    >
      {initials(user)}
    </span>
  )
}

export function AuthButton() {
  const { user, loading, signIn, signOut } = useAuth()

  if (loading) return null

  if (!user) {
    return (
      <button
        type="button"
        onClick={() => signIn().catch((error) => console.error('Sign-in failed', error))}
        className="inline-flex items-center gap-2 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <LogIn className="h-4 w-4" aria-hidden="true" />
        Sign in
      </button>
    )
  }

  return (
    <div className="flex items-center gap-3 text-sm text-gray-600">
      <Avatar key={user.uid} user={user} />
      <button
        type="button"
        onClick={() => signOut()}
        className="inline-flex items-center gap-2 rounded-md border border-gray-300 px-3 py-1.5 font-medium text-gray-700 hover:bg-gray-50"
      >
        <LogOut className="h-4 w-4" aria-hidden="true" />
        Sign out
      </button>
    </div>
  )
}
