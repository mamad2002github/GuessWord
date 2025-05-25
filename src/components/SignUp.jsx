import { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { toast } from 'react-toastify';

function SignUp() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: ''
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { signup } = useContext(AuthContext);
  const navigate = useNavigate();

  const validateField = (name, value) => {
    const newErrors = { ...errors };

    switch (name) {
      case 'username':
        if (!value) {
          newErrors.username = 'Username is required';
        } else if (!/^[a-zA-Z0-9@#$%^&*_-]{4,}$/.test(value)) {
          newErrors.username = 'Username must be at least 4 characters and contain only English letters, numbers, or @#$%^&*_-';
        } else {
          delete newErrors.username;
        }
        break;
      case 'password':
        if (!value) {
          newErrors.password = 'Password is required';
        } else if (!/^[a-zA-Z0-9@#$%^&*_-]{8,}$/.test(value)) {
          newErrors.password = 'Password must be at least 8 characters and contain only English letters, numbers, or @#$%^&*_-';
        } else {
          delete newErrors.password;
        }
        break;
      case 'confirm_password':
        if (!value) {
          newErrors.confirm_password = 'Confirm password is required';
        } else if (value !== formData.password) {
          newErrors.confirm_password = 'Passwords do not match';
        } else {
          delete newErrors.confirm_password;
        }
        break;
      case 'first_name':
        if (!value) {
          newErrors.first_name = 'First name is required';
        } else if (!/^[\p{L}]{2,}$/u.test(value)) {
          newErrors.first_name = 'First name must be at least 2 characters and contain only letters';
        } else {
          delete newErrors.first_name;
        }
        break;
      case 'last_name':
        if (!value) {
          newErrors.last_name = 'Last name is required';
        } else if (!/^[\p{L}]{2,}$/u.test(value)) {
          newErrors.last_name = 'Last name must be at least 2 characters and contain only letters';
        } else {
          delete newErrors.last_name;
        }
        break;
      default:
        break;
    }

    setErrors(newErrors);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    validateField(name, value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate all fields before submitting
    Object.keys(formData).forEach((name) => validateField(name, formData[name]));

    if (Object.keys(errors).length > 0) {
      toast.error('Please fix the errors in the form');
      return;
    }

    try {
      const success = await signup(formData);
      if (success) {
        toast.success('Signed up successfully!');
        navigate('/home');
      } else {
        toast.error('Error signing up. Please try again.');
      }
    } catch (error) {
      const serverErrors = error.response?.data || {};
      if (serverErrors.username) {
        setErrors({ ...errors, username: serverErrors.username });
      } else if (serverErrors.non_field_errors) {
        toast.error(serverErrors.non_field_errors);
      } else {
        toast.error('Error signing up. Check your inputs.');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Sign Up</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${errors.username ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {errors.username && (
              <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.username}</p>
            )}
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">First Name</label>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${errors.first_name ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {errors.first_name && (
              <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.first_name}</p>
            )}
          </div>
          <div className="mb-4">
            <label className="block text-gray-700">Last Name</label>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className={`w-full p-2 border rounded ${errors.last_name ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            {errors.last_name && (
              <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.last_name}</p>
            )}
          </div>
          <div className="mb-4 relative">
            <label className="block text-gray-700">Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`w-full p-2 pr-10 border rounded ${errors.password ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2 top-9 text-gray-500 hover:text-gray-700"
            >
              {showPassword ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
            {errors.password && (
              <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.password}</p>
            )}
          </div>
          <div className="mb-6 relative">
            <label className="block text-gray-700">Confirm Password</label>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              className={`w-full p-2 pr-10 border rounded ${errors.confirm_password ? 'border-red-500' : 'border-gray-300'}`}
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-2 top-9 text-gray-500 hover:text-gray-700"
            >
              {showConfirmPassword ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
            {errors.confirm_password && (
              <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.confirm_password}</p>
            )}
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white p-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
            disabled={Object.keys(errors).length > 0}
          >
            Sign Up
          </button>
        </form>
        <p className="mt-4 text-center">
          Already have an account? <a href="/" className="text-blue-500">Login</a>
        </p>
      </div>
    </div>
  );
}

export default SignUp;