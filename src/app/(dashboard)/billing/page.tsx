'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { createClient } from '@/supabase/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, CreditCard, Calendar, Check, ExternalLink } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import type { User, Subscription } from '@/types';

export default function BillingPage() {
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingPortal, setLoadingPortal] = useState(false);
  
  const supabase = createClient();

  useEffect(() => {
    const fetchData = async () => {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (!authUser) return;

      const [userData, subscriptionData] = await Promise.all([
        supabase
          .from('users')
          .select('*')
          .eq('id', authUser.id)
          .single(),
        supabase
          .from('subscriptions')
          .select('*')
          .eq('user_id', authUser.id)
          .single(),
      ]);

      if (userData.data) setUser(userData.data as User);
      if (subscriptionData.data) setSubscription(subscriptionData.data);
      setLoading(false);
    };
    fetchData();
  }, [supabase]);

  const openBillingPortal = async () => {
    setLoadingPortal(true);
    try {
      const response = await fetch('/api/billing/portal', { method: 'POST' });
      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error('Failed to open billing portal');
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to open billing portal', variant: 'destructive' });
    } finally {
      setLoadingPortal(false);
    }
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold mb-2">Billing</h1>
        <p className="text-muted-foreground">Manage your subscription and payment methods</p>
      </motion.div>

      <div className="space-y-6">
        <Card className="glass">
          <CardHeader>
            <CardTitle>Current Plan</CardTitle>
            <CardDescription>Your active subscription</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                  <CreditCard className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-lg font-medium">
                      {user?.subscription_tier === 'pro' ? 'Pro Plan' : 'Free Plan'}
                    </p>
                    <Badge
                      variant={subscription?.status === 'active' ? 'success' : 'warning'}
                    >
                      {subscription?.status || 'active'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {user?.subscription_tier === 'pro' ? '$19/month' : 'Free forever'}
                  </p>
                </div>
              </div>
              {user?.subscription_tier === 'pro' && (
                <Button onClick={openBillingPortal} disabled={loadingPortal}>
                  {loadingPortal ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Manage Billing
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {subscription && (
          <Card className="glass">
            <CardHeader>
              <CardTitle>Subscription Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="p-4 rounded-xl bg-muted/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Current Period</p>
                  </div>
                  <p className="font-medium">
                    {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-muted/30">
                  <div className="flex items-center gap-2 mb-2">
                    <CreditCard className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">Status</p>
                  </div>
                  <p className="font-medium capitalize">{subscription.status}</p>
                </div>
              </div>

              {subscription.cancel_at_period_end && (
                <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                  <p className="text-sm text-yellow-600 dark:text-yellow-500">
                    Your subscription will be canceled at the end of the current billing period.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <Card className="glass">
          <CardHeader>
            <CardTitle>Plan Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Resume analysis with ATS scoring</span>
              </div>
              <div className="flex items-center gap-2">
                <Check className="w-5 h-5 text-green-500" />
                <span>Keyword optimization</span>
              </div>
              <div className={`flex items-center gap-2 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground' : ''}`}>
                <Check className={`w-5 h-5 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground/50' : 'text-green-500'}`} />
                <span>Cover letter generation</span>
              </div>
              <div className={`flex items-center gap-2 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground' : ''}`}>
                <Check className={`w-5 h-5 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground/50' : 'text-green-500'}`} />
                <span>LinkedIn optimization</span>
              </div>
              <div className={`flex items-center gap-2 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground' : ''}`}>
                <Check className={`w-5 h-5 ${user?.subscription_tier !== 'pro' ? 'text-muted-foreground/50' : 'text-green-500'}`} />
                <span>Unlimited analyses</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
