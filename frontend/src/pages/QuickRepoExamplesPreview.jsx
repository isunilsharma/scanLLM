import React, { useState } from 'react';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Card } from '../components/ui/card';

const EXAMPLE_REPOS = [
  { 
    name: 'LLMs from Scratch', 
    url: 'https://github.com/rasbt/LLMs-from-scratch',
    description: 'Educational LLM implementation',
    icon: '📚'
  },
  { 
    name: 'Transformers', 
    url: 'https://github.com/huggingface/transformers',
    description: 'HuggingFace library',
    icon: '🤗'
  },
  { 
    name: 'Hands-On LLMs', 
    url: 'https://github.com/HandsOnLLM/Hands-On-Large-Language-Models',
    description: 'Practical LLM guide',
    icon: '✋'
  },
  { 
    name: 'Awesome LLM', 
    url: 'https://github.com/Hannibal046/Awesome-LLM',
    description: 'Curated LLM resources',
    icon: '⭐'
  }
];

const QuickRepoExamplesPreview = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            "Try an Example Repo" - UX Design Options
          </h1>
          <p className="text-gray-600">
            Compare different design approaches for quick repo selection
          </p>
        </div>

        <div className="space-y-12">
          {/* Option 1: Dropdown on Focus */}
          <VariantCard
            title="Option 1: Dropdown on Input Focus"
            description="When user clicks input field, dropdown appears below with example repos"
          >
            <Option1Dropdown />
          </VariantCard>

          {/* Option 2: Chip Pills Below Input */}
          <VariantCard
            title="Option 2: Pill Chips Below Input"
            description="Example repos shown as clickable pills always visible below the input"
          >
            <Option2Pills />
          </VariantCard>

          {/* Option 3: Quick Access Menu Button */}
          <VariantCard
            title="Option 3: Quick Access Menu Button"
            description="Small 'Examples' button next to input that opens a menu"
          >
            <Option3MenuButton />
          </VariantCard>

          {/* Option 4: Inline Suggestions (Autocomplete Style) */}
          <VariantCard
            title="Option 4: Autocomplete Suggestions"
            description="Type-to-filter suggestions that appear as you type"
          >
            <Option4Autocomplete />
          </VariantCard>
        </div>
      </div>
    </div>
  );
};

// Container for each variant
const VariantCard = ({ title, description, children }) => (
  <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
    <div className="mb-6 pb-4 border-b border-gray-200">
      <h2 className="text-2xl font-semibold text-gray-900 mb-2">{title}</h2>
      <p className="text-sm text-gray-600">{description}</p>
    </div>
    {children}
  </div>
);

// Option 1: Dropdown on Focus
const Option1Dropdown = () => {
  const [focused, setFocused] = useState(false);
  const [value, setValue] = useState('');

  return (
    <div className="max-w-2xl mx-auto">
      <div className="relative">
        <Input
          placeholder="https://github.com/owner/repo"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          className="h-12"
        />
        
        {/* Dropdown appears on focus */}
        {focused && (
          <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-xl">
            <div className="p-3 border-b border-gray-100">
              <p className="text-xs font-medium text-gray-700">Try an example repository</p>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {EXAMPLE_REPOS.map((repo, idx) => (
                <button
                  key={idx}
                  onClick={() => setValue(repo.url)}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{repo.icon}</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{repo.name}</p>
                      <p className="text-xs text-gray-500">{repo.description}</p>
                    </div>
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500 italic">
          ☝️ Click the input field to see example repos
        </p>
      </div>
    </div>
  );
};

// Option 2: Pills Below Input
const Option2Pills = () => {
  const [value, setValue] = useState('');

  return (
    <div className="max-w-2xl mx-auto">
      <Input
        placeholder="https://github.com/owner/repo"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="h-12"
      />
      
      {/* Pills always visible */}
      <div className="mt-4">
        <p className="text-xs text-gray-600 mb-2">Quick examples:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_REPOS.map((repo, idx) => (
            <button
              key={idx}
              onClick={() => setValue(repo.url)}
              className="inline-flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-full text-xs font-medium text-gray-700 transition-colors"
            >
              <span>{repo.icon}</span>
              <span>{repo.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

// Option 3: Menu Button
const Option3MenuButton = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [value, setValue] = useState('');

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            placeholder="https://github.com/owner/repo"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="h-12"
          />
        </div>
        
        {/* Examples button */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="h-12 px-4 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm font-medium text-gray-700"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Examples
          </button>
          
          {/* Dropdown menu */}
          {menuOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-10">
              <div className="p-3 border-b border-gray-100">
                <p className="text-xs font-medium text-gray-700">Try an example repository</p>
              </div>
              {EXAMPLE_REPOS.map((repo, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setValue(repo.url);
                    setMenuOpen(false);
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{repo.icon}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{repo.name}</p>
                      <p className="text-xs text-gray-500">{repo.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500 italic">
          ☝️ Click "Examples" button to see quick links
        </p>
      </div>
    </div>
  );
};

// Option 4: Autocomplete
const Option4Autocomplete = () => {
  const [value, setValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);

  const filteredRepos = EXAMPLE_REPOS.filter(repo => 
    value.length === 0 || 
    repo.name.toLowerCase().includes(value.toLowerCase()) ||
    repo.url.toLowerCase().includes(value.toLowerCase())
  );

  return (
    <div className="max-w-2xl mx-auto">
      <div className="relative">
        <Input
          placeholder="https://github.com/owner/repo or try typing 'transformers'"
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          className="h-12"
        />
        
        {/* Autocomplete suggestions */}
        {showSuggestions && filteredRepos.length > 0 && (
          <div className="absolute z-10 w-full mt-2 bg-white border border-gray-200 rounded-lg shadow-xl">
            <div className="p-3 border-b border-gray-100 flex items-center justify-between">
              <p className="text-xs font-medium text-gray-700">
                {value.length === 0 ? 'Example repositories' : 'Suggestions'}
              </p>
              <Badge variant="secondary" className="text-xs">
                {filteredRepos.length}
              </Badge>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {filteredRepos.map((repo, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setValue(repo.url);
                    setShowSuggestions(false);
                  }}
                  className="w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors border-b border-gray-50 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{repo.icon}</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{repo.name}</p>
                      <p className="text-xs text-gray-500 font-mono truncate">{repo.url}</p>
                    </div>
                    <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500 italic">
          ☝️ Click input or start typing to see suggestions
        </p>
      </div>
    </div>
  );
};

export default QuickRepoExamplesPreview;
