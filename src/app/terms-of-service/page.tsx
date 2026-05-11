export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-muted-foreground mb-8">Last updated: January 2024</p>
        
        <div className="prose prose-lg dark:prose-invert max-w-none space-y-6">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing or using ResumeIQ AI, you agree to be bound by these Terms of Service. 
              If you do not agree, please do not use our services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
            <p>
              ResumeIQ AI provides AI-powered resume optimization services, including ATS score analysis, 
              cover letter generation, and LinkedIn profile optimization. These services are provided 
              "as is" without warranties.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
            <p>
              You are responsible for maintaining the confidentiality of your account credentials. 
              You agree to notify us immediately of any unauthorized use of your account.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Acceptable Use</h2>
            <p>
              You agree not to use ResumeIQ AI for any illegal purposes or in violation of any laws. 
              You must not attempt to gain unauthorized access to our systems or other users' data.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Subscriptions and Payments</h2>
            <p>
              Pro subscriptions are billed monthly at $19/month. You can cancel anytime, and your 
              access continues until the end of the billing period. No refunds are provided for 
              partial months.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Limitation of Liability</h2>
            <p>
              ResumeIQ AI is not responsible for job placement outcomes. Our AI suggestions are 
              recommendations and do not guarantee interview calls or job offers.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Changes to Terms</h2>
            <p>
              We reserve the right to modify these terms at any time. Continued use of the service 
              after changes constitutes acceptance of the new terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">8. Contact</h2>
            <p>
              For questions about these Terms, contact us at legal@resumepro.ai.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
