import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Sparkles, AlertCircle } from 'lucide-react';
import { z } from 'zod';
import { Button } from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { useAuth } from '../../hooks/useAuth';
import { AuthLayoutShell } from './AuthLayoutShell';

const registerFormSchema = z
  .object({
    full_name: z.string().min(2, 'Full name must be at least 2 characters'),
    email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isAuthenticated } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    full_name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setFieldErrors({});

    const validationResult = registerFormSchema.safeParse({
      full_name: fullName,
      email,
      password,
      confirmPassword,
    });

    if (!validationResult.success) {
      const formatted = validationResult.error.format();
      setFieldErrors({
        full_name: formatted.full_name?._errors[0],
        email: formatted.email?._errors[0],
        password: formatted.password?._errors[0],
        confirmPassword: formatted.confirmPassword?._errors[0],
      });
      return;
    }

    setLoading(true);

    try {
      await register({
        full_name: fullName,
        email,
        password,
        role: 'CANDIDATE',
      });
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err instanceof Error ? err.message : 'Registration failed. Please check server connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayoutShell>
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pb-4">
          <CardTitle className="text-2xl font-bold text-neutral-900 dark:text-white font-display">
            Create an Account
          </CardTitle>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
            Join InterviewSage to launch personalized multi-agent interview simulations.
          </p>
        </CardHeader>

        <CardContent className="px-0 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-medium text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1">
              <label htmlFor="full_name" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Full Name
              </label>
              <input
                id="full_name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                placeholder="Jane Doe"
                required
              />
              {fieldErrors.full_name && (
                <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">{fieldErrors.full_name}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="email" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                placeholder="you@company.com"
                required
              />
              {fieldErrors.email && (
                <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 pr-10 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                  placeholder="At least 8 characters"
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600 dark:hover:text-white"
                  onClick={() => setShowPassword((prev) => !prev)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {fieldErrors.password && (
                <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">{fieldErrors.password}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="confirmPassword" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                placeholder="Re-enter your password"
                required
              />
              {fieldErrors.confirmPassword && (
                <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">
                  {fieldErrors.confirmPassword}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-3 shadow-md shadow-blue-600/25 transition-all focus:ring-2 focus:ring-blue-500 mt-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Sparkles className="mr-1.5 h-4 w-4 animate-spin" /> Creating Account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>
          </form>

          {/* Footer Login Link */}
          <div className="pt-2 text-center text-xs text-neutral-600 dark:text-neutral-400">
            Already have an account?{' '}
            <Link to="/login" className="font-bold text-blue-600 hover:underline dark:text-blue-400">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </AuthLayoutShell>
  );
}
