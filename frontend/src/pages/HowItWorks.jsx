import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';

const HowItWorks = () => {
  const navigate = useNavigate();

  const steps = [
    {
      number: 1,
      title: 'Point us at your repo',
      description: 'Enter a public GitHub repository URL. We clone it in a temporary workspace and never store the code itself beyond the scan.',
      icon: (
        <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      )
    },
    {
      number: 2,
      title: 'We scan for AI/LLM usage',
      description: 'Our scanner walks your codebase and uses configurable regex rules to detect LLM usage patterns across OpenAI, Anthropic, LangChain, Transformers, vLLM, and generic RAG constructs.',
      icon: (
        <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      )
    },
    {
      number: 3,
      title: 'You review the results',
      description: 'We aggregate findings by file and framework, so you can see which services call which AI frameworks, where prompts live, and where you might have shadow AI usage or deprecated patterns.',
      icon: (
        <svg className="w-12 h-12 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    }
  ];

  const detections = [
    'Direct SDK calls (e.g. openai.ChatCompletion, client.chat.completions.create)',
    'Framework usage (langchain, llama_index, transformers, vllm)',
    'Common RAG patterns (vectorstore, as_retriever())',
    'Locations of AI-related code per file'
  ];

  return (
    <div className="min-h-screen bg-background py-16">
      <div className="max-w-5xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            How ScanLLM.ai Works
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From GitHub URL to a clear view of your AI dependencies in just a few steps.
          </p>
        </div>

        {/* Steps */}
        <div className="space-y-12 mb-16">
          {steps.map((step) => (
            <div key={step.number} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200">
              <div className="flex flex-col md:flex-row gap-6 items-start">
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                    {step.icon}
                  </div>
                  <div className="text-center">
                    <span className="inline-block bg-primary text-white text-sm font-bold rounded-full w-8 h-8 flex items-center justify-center">
                      {step.number}
                    </span>
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                    {step.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* What we detect */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-200 mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">
            What we detect today
          </h2>
          <ul className="space-y-3">
            {detections.map((item, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <svg className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        <div className="bg-primary/5 rounded-2xl p-8 text-center border border-primary/20">
          <p className="text-lg text-gray-900 mb-6">
            Want to see this on your own repo? Head back to the Home page and run your first scan.
          </p>
          <Button
            onClick={() => navigate('/')}
            size="lg"
            className="bg-primary hover:bg-primary/90"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Run a Scan
          </Button>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;
