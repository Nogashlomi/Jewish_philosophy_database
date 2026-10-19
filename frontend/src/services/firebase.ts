import { initializeApp } from 'firebase/app'
import { getAnalytics, isSupported } from 'firebase/analytics'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'

const firebaseConfig = {
  apiKey: 'AIzaSyD-PwRMwiHXWWVVuhhob6YDWnB-VKtQyPA',
  authDomain: 'jephy-db.firebaseapp.com',
  projectId: 'jephy-db',
  storageBucket: 'jephy-db.firebasestorage.app',
  messagingSenderId: '308381421679',
  appId: '1:308381421679:web:3e41c48b0339403fce7d9a',
  measurementId: 'G-GFYSZXC905',
}

export const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()

isSupported().then((supported) => {
  if (supported) getAnalytics(app)
})
