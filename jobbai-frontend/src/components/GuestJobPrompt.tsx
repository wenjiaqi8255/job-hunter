import { Link } from 'react-router-dom'

function GuestJobPrompt() {
  return (
    <div className="bg-white rounded-lg p-6 text-center">
      <div className="text-4xl mb-4">🔐</div>
      
      <h3 className="text-lg font-bold text-textPrimary mb-2">
        Save Your Progress
      </h3>
      
      <p className="text-textSecondary mb-6">
        Log in or sign up to save jobs, track your application status, and add notes.
      </p>
      
      <Link
        to="/login"
        className="inline-block w-full bg-primary text-textPrimary py-2.5 px-4 rounded-lg text-sm font-bold hover:bg-primaryHover"
      >
        Login / Sign Up
      </Link>
      
      <div className="mt-4 text-xs text-textSecondary">
        <div className="flex items-center justify-center space-x-4">
          <span>✔️ Save Jobs</span>
          <span>✔️ Track Status</span>
          <span>✔️ Add Notes</span>
        </div>
      </div>
    </div>
  )
}

export default GuestJobPrompt
