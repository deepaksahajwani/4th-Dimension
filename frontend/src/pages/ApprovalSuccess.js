import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, ArrowRight } from 'lucide-react';

function ApprovalSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(5);

  const action = searchParams.get('action'); // 'approved' or 'rejected'
  const userName = searchParams.get('user');

  const isApproval = action === 'approved';

  useEffect(() => {
    // Countdown timer
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // Check if user is logged in
          const token = localStorage.getItem('token');
          if (token) {
            navigate('/dashboard');
          } else {
            navigate('/login');
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [navigate]);

  const handleContinue = () => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 text-center">
        {/* Icon */}
        <div className="mb-6">
          {isApproval ? (
            <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
          ) : (
            <div className="mx-auto w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
              <XCircle className="w-12 h-12 text-red-600" />
            </div>
          )}
        </div>

        {/* Title */}
        <h1
          className={`text-3xl font-bold mb-3 ${
            isApproval ? 'text-green-600' : 'text-red-600'
          }`}
        >
          {isApproval ? 'User Approved! ✓' : 'User Rejected'}
        </h1>

        {/* Message */}
        <p className="text-gray-600 text-lg mb-6">
          {isApproval ? (
            <>
              <strong className="text-gray-800">{userName || 'The user'}</strong> has been
              successfully approved and notified via email.
            </>
          ) : (
            <>
              <strong className="text-gray-800">{userName || 'The user'}</strong> has been
              rejected and notified via email.
            </>
          )}
        </p>

        {/* Additional Info */}
        {isApproval && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm text-blue-900">
              <strong>✉️ Email Sent:</strong> A personalized welcome email with login
              instructions has been sent to the user.
            </p>
          </div>
        )}

        {/* Auto-redirect message */}
        <p className="text-sm text-gray-500 mb-6">
          Redirecting to your dashboard in <strong className="text-indigo-600">{countdown}</strong>{' '}
          seconds...
        </p>

        {/* Continue Button */}
        <button
          onClick={handleContinue}
          className="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 group"
        >
          Continue to Dashboard
          <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
        </button>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            4th Dimension - Architecture & Design
          </p>
        </div>
      </div>
    </div>
  );
}

export default ApprovalSuccess;
