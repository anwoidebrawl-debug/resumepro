export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-muted-foreground mb-8">Last updated: January 2024</p>
        
        <div className="prose prose-lg dark:prose-invert max-w-none space-y-6">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Information We Collect</h2>
            <p>
              ResumeIQ AI collects information you provide directly, including your name, email address, 
              and resume content when you use our service. We also collect usage data to improve our services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. How We Use Your Information</h2>
            <p>
              We use your information to provide AI-powered resume analysis, generate cover letters, 
              and improve our services. Your resume content is processed by AI models to provide 
              optimization suggestions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. Data Security</h2>
            <p>
              We implement industry-standard encryption to protect your data. Resume files are stored 
              securely and can be deleted at any time. We never sell your personal information to third parties.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Cookies</h2>
            <p>
              We use cookies to maintain your session and remember your preferences. You can disable 
              cookies in your browser settings, but some features may not work properly.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Your Rights</h2>
            <p>
              You have the right to access, correct, or delete your personal data. Contact us at 
              privacy@resumepro.ai for any privacy-related requests.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy, please contact us at 
              privacy@resumepro.ai.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
