import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Sparkles, AlertCircle, ShieldAlert } from 'lucide-react';
import { z } from 'zod';
import { Button } from '../../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { useAuth } from "../../hooks/useAuth";
import { AuthLayoutShell } from './AuthLayoutShell';

const signInSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Invalid email format'),
  password: z.string().min(1, 'Password is required'),
});

export function AuthPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warningBanner, setWarningBanner] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setWarningBanner(null);
    setFieldErrors({});

    const validationResult = signInSchema.safeParse({ email, password });
    if (!validationResult.success) {
      const formatted = validationResult.error.format();
      setFieldErrors({
        email: formatted.email?._errors[0],
        password: formatted.password?._errors[0],
      });
      return;
    }

    setLoading(true);

    try {
      await login({ email, password });
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 401) {
        setError('Incorrect email or password. Please try again.');
      } else if (status === 403) {
        setWarningBanner('Your account requires verification. Please check your inbox or resend verification email.');
      } else if (status === 429) {
        setWarningBanner('Too many login attempts. Please wait 60 seconds before trying again.');
      } else {
        setError(err instanceof Error ? err.message : 'Authentication failed. Please check server connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayoutShell>
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pb-4">
          <CardTitle className="text-2xl font-bold text-neutral-900 dark:text-white font-display">
            Sign in to InterviewSage
          </CardTitle>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-400">
            Welcome back! Enter your credentials to access your mock sessions.
          </p>
        </CardHeader>

        <CardContent className="px-0 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs font-medium text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {warningBanner && (
            <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-medium text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300">
              <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
              <span>{warningBanner}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1">
              <label htmlFor="email" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                placeholder="you@company.com"
                required
              />
              {fieldErrors.email && (
                <p className="text-[11px] font-semibold text-rose-600 dark:text-rose-400">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                  Password
                </label>
                <a href="#forgot" className="text-[11px] font-semibold text-blue-600 hover:underline dark:text-blue-400">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 pr-10 text-xs text-neutral-900 shadow-2xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950 dark:text-white transition-all"
                  placeholder="Enter your password"
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

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-xs font-medium text-neutral-600 dark:text-neutral-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-neutral-300 text-blue-600 focus:ring-blue-500 dark:border-neutral-700 dark:bg-neutral-900"
                />
                <span>Remember me for 30 days</span>
              </label>
            </div>

            <Button
              type="submit"
              className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-3 shadow-md shadow-blue-600/25 transition-all focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Sparkles className="mr-1.5 h-4 w-4 animate-spin" /> Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-4 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-neutral-200 dark:border-neutral-800" />
            </div>
            <span className="relative bg-white dark:bg-neutral-950 px-3 text-[11px] font-semibold text-neutral-400 uppercase font-mono">
              or continue with
            </span>
          </div>

          {/* OAuth Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => alert('Google OAuth Sign In triggered')}
              className="rounded-xl border-neutral-200 text-xs font-semibold dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900"
            >
              Google
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => alert('GitHub OAuth Sign In triggered')}
              className="rounded-xl border-neutral-200 text-xs font-semibold dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900"
            >
              GitHub
            </Button>
          </div>

          {/* Footer Register Link */}
          <div className="pt-2 text-center text-xs text-neutral-600 dark:text-neutral-400">
            Need an account?{' '}
            <Link to="/register" className="font-bold text-blue-600 hover:underline dark:text-blue-400">
              Create one
            </Link>
          </div>
        </CardContent>
      </Card>
    </AuthLayoutShell>
  );
}
