import { getApps, initializeApp } from 'firebase/app'
import {
  GoogleAuthProvider,
  getRedirectResult,
  getAuth,
  signInWithPopup,
  signInWithRedirect,
  signOut,
  type Auth,
  type User,
} from 'firebase/auth'

export interface RealGoogleUser {
  uid: string
  email: string
  displayName: string
  photoURL?: string | null
  idToken: string
}

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyA27G3pbkjiYXHNxnP0lMrteYXTQ9Q6fAY',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'patient-1d860.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'patient-1d860',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:381526778497:web:fa4028bd4ffd843a3ea380',
}

function getFirebaseAuth(): Auth {
  const app = getApps()[0] ?? initializeApp(firebaseConfig)
  return getAuth(app)
}

function createGoogleProvider(): GoogleAuthProvider {
  const provider = new GoogleAuthProvider()
  provider.addScope('email')
  provider.addScope('profile')
  provider.setCustomParameters({ prompt: 'select_account' })
  return provider
}

async function toRealGoogleUser(user: User, auth: Auth): Promise<RealGoogleUser> {
  const email = user.email
  if (!email || !user.emailVerified) {
    await signOut(auth)
    throw new Error('Google did not provide a verified email address for this account.')
  }

  return {
    uid: user.uid,
    email,
    displayName: user.displayName || email,
    photoURL: user.photoURL,
    idToken: await user.getIdToken(),
  }
}

export async function signInWithGoogle(): Promise<RealGoogleUser> {
  const auth = getFirebaseAuth()
  const result = await signInWithPopup(auth, createGoogleProvider())
  return toRealGoogleUser(result.user, auth)
}

export async function startGoogleRedirectSignIn(): Promise<void> {
  const auth = getFirebaseAuth()
  await signInWithRedirect(auth, createGoogleProvider())
}

export async function getGoogleRedirectUser(): Promise<RealGoogleUser | null> {
  const auth = getFirebaseAuth()
  const result = await getRedirectResult(auth)
  return result ? toRealGoogleUser(result.user, auth) : null
}

export async function signOutFromGoogle(): Promise<void> {
  const app = getApps()[0]
  if (app) await signOut(getAuth(app))
}
