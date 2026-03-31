import React from 'react';
import { FileText } from 'lucide-react';

const Terms = () => {
  const lastUpdated = 'March 28, 2026';

  const sections = [
    {
      title: '1. Acceptance of Terms',
      content: [
        {
          text: 'By accessing or using ScanLLM ("Service"), you agree to be bound by these Terms of Service ("Terms"). If you are using the Service on behalf of an organization, you represent and warrant that you have the authority to bind that organization to these Terms. If you do not agree to these Terms, do not use the Service.',
        },
      ],
    },
    {
      title: '2. Description of Service',
      content: [
        {
          text: 'ScanLLM is an AI dependency intelligence platform that provides:',
          list: [
            'Code scanning to detect AI/LLM dependencies, frameworks, and security patterns',
            'Interactive dependency graph visualization',
            'Risk scoring and OWASP LLM Top 10 vulnerability mapping',
            'Policy-as-code enforcement for CI/CD pipelines',
            'AI Bill of Materials (AI-BOM) generation in CycloneDX format',
            'Drift detection and historical scan comparison',
            'A command-line interface (CLI) for local scanning',
            'A web-based dashboard for team collaboration (paid tiers)',
          ],
        },
      ],
    },
    {
      title: '3. Service Tiers',
      content: [
        {
          subtitle: '3.1 Community Edition (Free)',
          text: 'The ScanLLM CLI and open-source scanning engine are available under the MIT License. You may use, modify, and distribute the CLI in accordance with the MIT License terms. Community Edition includes: local scanning, JSON/SARIF/CycloneDX output, policy checking, and the signature database.',
        },
        {
          subtitle: '3.2 Team Edition (Paid)',
          text: 'The Team tier provides additional cloud-hosted features: multi-repo scanning, organizational dashboard, scan history retention, trend reporting, and team management. Pricing is per-seat, billed monthly or annually.',
        },
        {
          subtitle: '3.3 Enterprise Edition (Paid)',
          text: 'The Enterprise tier includes all Team features plus: SSO/SAML integration, audit logging, API access, custom integrations, SLA guarantees, and dedicated support. Contact us for pricing.',
        },
      ],
    },
    {
      title: '4. Account Terms',
      content: [
        {
          text: 'To use certain features of the Service, you must create an account via GitHub OAuth. You agree to:',
          list: [
            'Provide accurate and complete information',
            'Maintain the security of your account credentials',
            'Promptly notify us of any unauthorized access or use of your account',
            'Accept responsibility for all activities that occur under your account',
            'Not share your account with unauthorized users',
          ],
        },
        {
          text: 'We reserve the right to suspend or terminate accounts that violate these Terms or engage in abusive behavior.',
        },
      ],
    },
    {
      title: '5. Acceptable Use',
      content: [
        {
          subtitle: '5.1 Permitted Use',
          text: 'You may use ScanLLM to scan repositories that you own or have explicit authorization to scan. You may use scan results for internal security analysis, compliance reporting, and AI governance purposes.',
        },
        {
          subtitle: '5.2 Prohibited Use',
          text: 'You agree NOT to:',
          list: [
            'Scan repositories without authorization from the repository owner',
            'Use the Service to discover and exploit vulnerabilities in third-party systems',
            'Attempt to reverse-engineer, decompile, or extract proprietary algorithms from the Service',
            'Use the Service in violation of any applicable law or regulation',
            'Introduce malicious code, viruses, or harmful material through the Service',
            'Overwhelm the Service with automated requests beyond reasonable usage (rate limiting applies)',
            'Resell, sublicense, or redistribute the paid Service without authorization',
            'Use the Service to compete directly with ScanLLM without disclosure',
          ],
        },
      ],
    },
    {
      title: '6. Intellectual Property',
      content: [
        {
          subtitle: '6.1 Your Content',
          text: 'You retain all rights to your source code and repositories. ScanLLM does not claim ownership of any code you scan. Scan results (findings, risk scores, dependency graphs) generated from your code belong to you.',
        },
        {
          subtitle: '6.2 Our Property',
          text: 'The ScanLLM scanning engine, algorithms, user interface, documentation, and branding are owned by ScanLLM. The open-source CLI and core engine are licensed under the MIT License. The AI signatures database is community-maintained under the MIT License.',
        },
        {
          subtitle: '6.3 Feedback',
          text: 'If you provide feedback, suggestions, or ideas about the Service, you grant us a non-exclusive, royalty-free, worldwide license to use and incorporate that feedback into the Service.',
        },
      ],
    },
    {
      title: '7. Data and Privacy',
      content: [
        {
          text: 'Your use of the Service is also governed by our Privacy Policy, which describes how we collect, use, and protect your data. Key points:',
          list: [
            'Source code is NOT stored beyond the scan lifecycle',
            'Scan results are retained according to your tier\'s retention policy',
            'The CLI operates entirely locally unless you opt in to cloud features',
            'We do NOT sell your data',
            'You may export and delete your data at any time',
          ],
        },
      ],
    },
    {
      title: '8. Payment Terms',
      content: [
        {
          subtitle: '8.1 Billing',
          text: 'Paid plans are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by applicable law or as explicitly stated in your service agreement.',
        },
        {
          subtitle: '8.2 Price Changes',
          text: 'We may modify pricing with 30 days\' written notice. Price changes do not apply to the current billing period. If you disagree with a price change, you may cancel your subscription before the next billing period.',
        },
        {
          subtitle: '8.3 Taxes',
          text: 'All fees are exclusive of taxes. You are responsible for paying applicable sales, use, VAT, or other taxes, except for taxes based on ScanLLM\'s net income.',
        },
      ],
    },
    {
      title: '9. Service Availability and SLA',
      content: [
        {
          subtitle: '9.1 Availability',
          text: 'We strive to maintain 99.9% uptime for the cloud-hosted Service. The CLI operates independently and is not subject to service availability constraints.',
        },
        {
          subtitle: '9.2 Maintenance',
          text: 'We may perform scheduled maintenance with reasonable advance notice. Emergency maintenance may occur without notice when necessary to protect the security or integrity of the Service.',
        },
        {
          subtitle: '9.3 Enterprise SLA',
          text: 'Enterprise customers receive an SLA with defined uptime guarantees, response times, and remedies for service disruption. SLA terms are documented in your Enterprise agreement.',
        },
      ],
    },
    {
      title: '10. Limitation of Liability',
      content: [
        {
          text: 'TO THE MAXIMUM EXTENT PERMITTED BY LAW, SCANLLM SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF PROFITS OR REVENUE, WHETHER INCURRED DIRECTLY OR INDIRECTLY.',
        },
        {
          text: 'ScanLLM provides static code analysis and does NOT guarantee detection of all AI dependencies, security vulnerabilities, or compliance issues. The Service is a tool to assist your security and governance processes, not a replacement for comprehensive security review.',
        },
        {
          text: 'IN NO EVENT SHALL SCANLLM\'S TOTAL LIABILITY EXCEED THE AMOUNT PAID BY YOU FOR THE SERVICE DURING THE TWELVE (12) MONTHS PRIOR TO THE CLAIM.',
        },
      ],
    },
    {
      title: '11. Indemnification',
      content: [
        {
          text: 'You agree to indemnify, defend, and hold harmless ScanLLM from and against any claims, damages, losses, liabilities, and expenses arising from: (a) your use of the Service; (b) your violation of these Terms; (c) your violation of any third-party rights, including intellectual property rights; or (d) your scanning of repositories without proper authorization.',
        },
      ],
    },
    {
      title: '12. Termination',
      content: [
        {
          text: 'Either party may terminate the Service relationship at any time:',
          list: [
            'You may cancel your account at any time through the Settings page or by contacting support',
            'We may suspend or terminate your account for violation of these Terms with notice',
            'Upon termination, your right to access paid features ceases immediately',
            'You may export your data before termination',
            'Scan history is deleted within 30 days of account deletion',
            'Provisions that by their nature survive termination (including IP, limitation of liability, and indemnification) will survive',
          ],
        },
      ],
    },
    {
      title: '13. Governing Law and Dispute Resolution',
      content: [
        {
          text: 'These Terms are governed by the laws of the State of Delaware, United States, without regard to conflict of law principles. Any disputes arising from these Terms shall be resolved through binding arbitration under the rules of the American Arbitration Association, held in Delaware. Each party bears its own costs of arbitration.',
        },
      ],
    },
    {
      title: '14. Changes to Terms',
      content: [
        {
          text: 'We reserve the right to modify these Terms at any time. We will notify you of material changes by posting the updated Terms on this page and updating the "Last updated" date. For paid customers, material changes will also be communicated via email at least 30 days in advance. Continued use after changes constitutes acceptance.',
        },
      ],
    },
    {
      title: '15. Contact',
      content: [
        {
          text: 'For questions about these Terms, contact us at:',
          list: [
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
              <FileText className="w-5 h-5 text-cyan-400" />
            </div>
            <span className="text-sm text-cyan-400 font-medium">Legal</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">
            Terms of Service
          </h1>
          <p className="text-zinc-400 text-lg">
            Last updated: {lastUpdated}
          </p>
          <div className="mt-6 p-4 bg-zinc-900/80 border border-zinc-800 rounded-lg">
            <p className="text-zinc-400 text-sm leading-relaxed">
              <span className="text-zinc-200 font-medium">TL;DR: </span>
              Use ScanLLM to scan repos you own. The CLI is MIT licensed and free forever. Paid tiers add team/enterprise features. We don't own your code or sell your data.
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

export default Terms;
