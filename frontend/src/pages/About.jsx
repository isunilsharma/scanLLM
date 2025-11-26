import React from 'react';

const About = () => {
  return (
    <div className="min-h-screen bg-background py-16">
      <div className="max-w-4xl mx-auto px-6">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            About ScanLLM.ai
          </h1>
        </div>

        {/* Mission Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Our mission</h2>
          <p className="text-gray-700 leading-relaxed text-lg">
            ScanLLM.ai exists to give engineering teams a clear view of where AI actually lives inside their systems. 
            As companies race to adopt LLMs across dozens of services, it has become almost impossible to answer basic 
            questions like "Where are we calling OpenAI?" or "What breaks if we change this model?" We're building the 
            visibility layer for AI dependencies.
          </p>
        </section>

        {/* Beliefs Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">What we believe</h2>
          <ul className="space-y-4">
            {[
              'AI adoption should not mean AI chaos.',
              'Platform and security teams deserve a single source of truth for AI usage.',
              'Simple, static analysis can prevent expensive outages and compliance issues.',
              'Devtools should be fast, transparent, and easy to adopt.'
            ].map((belief, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <svg className="w-6 h-6 text-accent flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700 text-lg">{belief}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Future Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">Where we're going next</h2>
          <p className="text-gray-700 leading-relaxed text-lg">
            This initial scanner is just the first step. Over time, we'll expand into multi-repo mapping, CI integration, 
            blast-radius analysis for model upgrades, governance policies for AI usage, and deeper integration with your 
            observability and security stack.
          </p>
        </section>

        {/* Contact CTA */}
        <section className="bg-primary/5 rounded-2xl p-8 border border-primary/20">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Get in touch</h2>
          <p className="text-gray-700 mb-6">
            Interested in early access for your team? Book a live demo and tell us about your AI stack.
          </p>
          <a
            href="https://calendly.com/sunildec1991/30min"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Book a Demo
          </a>
        </section>
      </div>
    </div>
  );
};

export default About;
