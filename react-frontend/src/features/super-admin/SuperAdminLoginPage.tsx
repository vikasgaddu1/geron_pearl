/**
 * Super Admin Login Page
 * 
 * Separate login page for platform administrators.
 * Supports MFA authentication.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn, Loader2, Shield } from 'lucide-react';
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <Card className="w-full max-w-md shadow-2xl border-slate-700 bg-slate-800/50 backdrop-blur">
        <CardHeader className="space-y-3 text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
              <Shield className="h-8 w-8 text-white" />
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl font-bold text-white">
              Super Admin Portal
            </CardTitle>
            <p className="text-sm text-amber-500 mt-1">
              PEARL Platform Administration
            </p>
          </div>
          <CardDescription className="text-slate-400">
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
                  <Label htmlFor="email" className="text-slate-300">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="superadmin@pearl.local"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={isLoading}
                    autoComplete="email"
                    className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-slate-300">Password</Label>
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
                      className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500 pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="mfa" className="text-slate-300">MFA Code</Label>
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
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500 text-center text-2xl tracking-widest"
                />
                <Button
                  type="button"
                  variant="link"
                  className="text-slate-400 hover:text-white p-0 h-auto"
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
              className="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white"
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
