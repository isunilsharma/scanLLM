import React from 'react';
import { Shield } from 'lucide-react';

const Privacy = () => {
  const lastUpdated = 'March 28, 2026';

  const sections = [
    {
      title: '1. Information We Collect',
      content: [
        {
          subtitle: '1.1 Account Information',
          text: 'When you create an account via GitHub OAuth, we collect your GitHub username, email address, avatar URL, and organization memberships. This information is necessary to provide you with access to ScanLLM\'s features.',
        },
        {
          subtitle: '1.2 Repository Data',
          text: 'When you scan a repository, ScanLLM clones the repository into a temporary, isolated workspace. We analyze the code to detect AI/LLM dependencies, security patterns, and configuration issues. We do NOT store your source code beyond the duration of the scan. Only scan results (findings, dependency graphs, risk scores) are retained.',
        },
        {
          subtitle: '1.3 Scan Results',
          text: 'We store scan metadata including: file paths where findings were detected, line numbers, pattern matches, risk scores, OWASP classifications, and dependency relationships. This data is used to provide historical analysis, drift detection, and compliance reporting.',
        },
        {
          subtitle: '1.4 Usage Data',
          text: 'We collect anonymized usage metrics to improve ScanLLM, including: features used, scan frequency, error rates, and performance metrics. We do NOT track individual user behavior or sell usage data to third parties.',
        },
        {
          subtitle: '1.5 CLI Usage',
          text: 'The ScanLLM CLI tool operates entirely locally on your machine. No data is transmitted to our servers unless you explicitly opt in to cloud features (team dashboard, historical tracking). Local scans remain local.',
        },
      ],
    },
    {
      title: '2. How We Use Your Information',
      content: [
        {
          text: 'We use the information we collect to:',
          list: [
            'Provide, maintain, and improve ScanLLM\'s scanning and analysis services',
            'Generate AI-BOMs (AI Bill of Materials), risk reports, and compliance documents',
            'Detect AI dependency drift across scan history',
            'Enforce security policies configured by your team',
            'Send critical security notifications related to your scanned repositories',
            'Provide customer support and respond to your requests',
            'Comply with legal obligations',
          ],
        },
      ],
    },
    {
      title: '3. Data Sharing and Disclosure',
      content: [
        {
          subtitle: '3.1 No Sale of Data',
          text: 'We do NOT sell, rent, or trade your personal information or scan results to any third party. Period.',
        },
        {
          subtitle: '3.2 Service Providers',
          text: 'We use a limited number of service providers to operate ScanLLM: Render (hosting), GitHub (authentication and repository access). These providers are contractually obligated to protect your data.',
        },
        {
          subtitle: '3.3 Legal Requirements',
          text: 'We may disclose information if required by law, subpoena, or court order, or if we believe disclosure is necessary to protect our rights, your safety, or the safety of others.',
        },
        {
          subtitle: '3.4 Organizational Access',
          text: 'If you are part of an organization on ScanLLM, organization administrators may have access to scan results for repositories within that organization. Individual user accounts remain private.',
        },
      ],
    },
    {
      title: '4. Data Security',
      content: [
        {
          text: 'We implement industry-standard security measures to protect your data:',
          list: [
            'All data in transit is encrypted via TLS 1.3',
            'Repository clones are processed in isolated temporary directories and deleted immediately after scanning',
            'Database encryption at rest',
            'GitHub OAuth tokens are stored with encryption and scoped to minimum required permissions',
            'Regular security audits and dependency updates',
            'No source code is stored beyond the scan lifecycle',
          ],
        },
      ],
    },
    {
      title: '5. Data Retention',
      content: [
        {
          text: 'We retain your data as follows:',
          list: [
            'Source code: Deleted immediately after scan completion (not retained)',
            'Scan results: Retained for the duration of your account, or as required by your organization\'s retention policy',
            'Account data: Retained until you delete your account',
            'Audit logs: Retained for 12 months for security and compliance purposes',
            'Anonymized analytics: May be retained indefinitely in aggregate form',
          ],
        },
      ],
    },
    {
      title: '6. Your Rights',
      content: [
        {
          text: 'Depending on your jurisdiction, you may have the following rights:',
          list: [
            'Access: Request a copy of the data we hold about you',
            'Correction: Request correction of inaccurate data',
            'Deletion: Request deletion of your account and associated data',
            'Export: Download your scan history and findings in JSON or CycloneDX format',
            'Objection: Object to certain processing of your data',
            'Portability: Receive your data in a machine-readable format',
          ],
        },
        {
          text: 'To exercise these rights, contact us at privacy@scanllm.ai. We will respond within 30 days.',
        },
      ],
    },
    {
      title: '7. International Data Transfers',
      content: [
        {
          text: 'ScanLLM is hosted in the United States via Render. If you are accessing ScanLLM from outside the United States, your data may be transferred to, stored, and processed in the US. By using ScanLLM, you consent to this transfer. We comply with applicable data protection laws including GDPR for EU/EEA users.',
        },
      ],
    },
    {
      title: '8. Children\'s Privacy',
      content: [
        {
          text: 'ScanLLM is not directed at individuals under 16 years of age. We do not knowingly collect personal information from children. If you believe a child has provided us with personal information, please contact us and we will delete it.',
        },
      ],
    },
    {
      title: '9. Changes to This Policy',
      content: [
        {
          text: 'We may update this Privacy Policy from time to time. We will notify you of material changes by posting the updated policy on this page and updating the "Last updated" date. Continued use of ScanLLM after changes constitutes acceptance of the updated policy.',
        },
      ],
    },
    {
      title: '10. Contact Us',
      content: [
        {
          text: 'If you have questions about this Privacy Policy or our data practices, contact us at:',
          list: [
            'Email: privacy@scanllm.ai',
            'GitHub: github.com/isunilsharma/scanllm/issues',
            'LinkedIn: linkedin.com/company/scanllm-ai',
          ],
        },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Hero */}
      <section className="relative">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />
        <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-12">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-cyan-400" />
            </div>
            <span className="text-sm text-cyan-400 font-medium">Legal</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Privacy Policy
          </h1>
          <p className="text-zinc-400 text-lg">
            Last updated: {lastUpdated}
          </p>
          <div className="mt-6 p-4 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <p className="text-zinc-400 text-sm leading-relaxed">
              <span className="text-zinc-200 font-medium">TL;DR: </span>
              We don't store your source code. The CLI runs locally. Scan results are yours. We don't sell data. You can delete everything anytime.
            </p>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="space-y-10">
          {sections.map((section) => (
            <div key={section.title} className="border-t border-zinc-800/50 pt-8">
              <h2 className="text-xl font-semibold text-zinc-100 mb-5">{section.title}</h2>
              <div className="space-y-5">
                {section.content.map((block, idx) => (
                  <div key={idx}>
                    {block.subtitle && (
                      <h3 className="text-sm font-semibold text-zinc-300 mb-2">{block.subtitle}</h3>
                    )}
                    {block.text && (
                      <p className="text-zinc-400 text-sm leading-relaxed">{block.text}</p>
                    )}
                    {block.list && (
                      <ul className="mt-3 space-y-2">
                        {block.list.map((item, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                            <span className="w-1 h-1 rounded-full bg-zinc-600 flex-shrink-0 mt-2" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Privacy;
