/**
 * Super Admin Login Page
 * 
 * Separate login page for platform administrators.
 * Supports MFA authentication.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { superAdminLogin } from '@/api/endpoints/super-admin';

export function SuperAdminLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [requiresMfa, setRequiresMfa] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;
    if (requiresMfa && !mfaToken) return;

    setIsLoading(true);
    try {
      const response = await superAdminLogin({
        email,
        password,
        mfa_token: requiresMfa ? mfaToken : undefined,
      });

      if (response.requires_mfa && !response.access_token) {
        setRequiresMfa(true);
        toast.info('Please enter your MFA code');
      } else {
        toast.success('Login successful');
        navigate('/admin/dashboard');
      }
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md shadow-xl border-slate-200">
        <CardHeader className="space-y-3 text-center">
          <div className="flex justify-center">
            <div className="w-14 h-14 bg-teal-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">P</span>
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl font-bold text-slate-900">
              Super Admin Portal
            </CardTitle>
            <p className="text-sm text-teal-600 mt-1">
              PEARL Platform Administration
            </p>
          </div>
          <CardDescription>
            {requiresMfa
              ? 'Enter your MFA code to continue'
              : 'Sign in with your super admin credentials'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!requiresMfa ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="superadmin@pearl.local"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="email"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      disabled={isLoading}
                      autoComplete="current-password"
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="mfa">MFA Code</Label>
                <Input
                  id="mfa"
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={mfaToken}
                  onChange={(e) => setMfaToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  disabled={isLoading}
                  autoComplete="one-time-code"
                  maxLength={6}
                  className="text-center text-2xl tracking-widest"
                />
                <Button
                  type="button"
                  variant="link"
                  className="p-0 h-auto"
                  onClick={() => {
                    setRequiresMfa(false);
                    setMfaToken('');
                  }}
                >
                  ← Back to login
                </Button>
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-teal-600 hover:bg-teal-700 text-white"
              disabled={isLoading || !email || !password || (requiresMfa && mfaToken.length !== 6)}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <LogIn className="mr-2 h-4 w-4" />
                  {requiresMfa ? 'Verify MFA' : 'Sign In'}
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-xs text-slate-500">
              This is a restricted access area for platform administrators only.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
