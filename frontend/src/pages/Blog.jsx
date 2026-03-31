import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/badge';

const Blog = () => {
  const navigate = useNavigate();
  
  const blogs = [
    {
      id: 1,
      title: 'Why We Built ScanLLM.ai',
      category: 'Company & Vision',
      excerpt: 'When large language models first entered the enterprise, it was easy to understand where they lived. That moment didn\'t last long.',
      readTime: '5 min read',
      date: 'November 2025',
      featured: true,
      content: `When large language models first entered the enterprise, it was easy to understand where they lived. A single team owned the integration, the prompts lived in one place, and the workflow was contained. That moment didn't last long. As adoption accelerated, every team began building AI features, each with its own approach, its own framework, and its own assumptions. In a surprisingly short time, organizations lost the ability to answer a basic question: Where exactly are we using AI in our codebase?

We built ScanLLM.ai because this question kept resurfacing — not just as a curiosity, but as a source of operational risk. Companies struggled to standardize LLM usage because they had no visibility into what already existed. Platform and infra teams tried to enforce guidelines, only to realize they didn't know which services were bypassing them. Security teams grew nervous about data flowing through prompts they had never reviewed. Architects wanted to rationalize the AI stack, but they had no map of the landscape.

The more we looked, the clearer the pattern became. AI sprawl wasn't a technical problem; it was a visibility problem. Teams couldn't govern what they couldn't see. They couldn't upgrade models confidently because they didn't know what depended on them. They couldn't measure cost drivers because token usage was scattered across dozens of untracked endpoints. Every attempt to understand the system required days of code searches, manual scraping, and tribal knowledge.

ScanLLM.ai is our response to that reality — a way to give organizations a clear, accurate view of their AI footprint. Instead of relying on documentation or memory, we analyze the code directly. By surfacing where frameworks, prompts, and model calls live, we give engineering leaders the foundation they've been missing: the ability to understand their own AI infrastructure with precision.

This clarity is the first step toward everything else—governance, standardization, cost optimization, and reliable operations. We're not trying to replace your AI platform or observability stack. We're solving the layer that many teams overlooked until it became urgent: the map.

AI adoption is accelerating faster than tooling can keep up. But one principle hasn't changed: good engineering starts with understanding the system. ScanLLM.ai exists to bring that understanding back to the organizations building the future.`
    },
    {
      id: 2,
      title: 'The 7 Types of AI Sprawl Every Company Faces',
      category: 'Best Practices',
      excerpt: 'As organizations embrace LLMs, they often assume the biggest challenge will be scaling infrastructure or managing costs.',
      readTime: '6 min read',
      date: 'November 2025',
      featured: false,
      content: `As organizations embrace LLMs, they often assume the biggest challenge will be scaling infrastructure or managing costs. In practice, the hardest part turns out to be far more basic: keeping track of where AI has spread throughout the company. What begins as a single integration quickly evolves into a dispersed network of model calls, prompts, frameworks, and pipelines — most of which nobody has a complete view of.

One form of sprawl appears in the frameworks teams choose. A backend service might call OpenAI directly. Another might use Anthropic through a custom wrapper. A third might rely on LangChain abstractions. Over time, these decisions compound, and teams find themselves maintaining multiple patterns that do the same thing in slightly different ways.

Model versions introduce another layer of fragmentation. It's common to see deprecated models running quietly in production because upgrading them feels risky. Without full visibility into dependencies, teams postpone updates and accumulate technical debt that becomes harder to unwind.

Prompts introduce their own form of drift. They live in code, in configuration files, in shared documents, and occasionally in Slack threads that were never meant to serve as source control. When prompts change, they often change silently — without review, without testing, and without anyone tracking their evolution.

Retrieval-augmented generation adds even more complexity. Vector stores proliferate, embedding jobs kick off in unexpected places, and indexes grow stale. No one person knows which data has been embedded, how it's being retrieved, or who is responsible for maintaining it.

Shadow AI is another subtle form of sprawl. Developers experiment with LLMs, find something that works, and ship it quickly. Those integrations aren't always routed through the intended gateway or reviewed by the platform team. They remain undocumented until something breaks or a compliance review uncovers them.

Microservice environments amplify everything. When dozens of services call LLMs in different ways, operational consistency vanishes. Error handling, fallback logic, safety checks, and logging vary widely — often without anyone noticing.

And finally, there's the financial layer. Token usage grows organically, without monitoring or ownership. Small inefficiencies spread across services snowball into significant, unexpected spend.

AI sprawl is not the result of poor engineering. It's the natural outcome of fast-moving teams working with fast-evolving tools. But as organizations mature their AI strategy, they need a clear picture of what they've built — not to restrict innovation, but to protect it. Understanding the forms that AI sprawl takes is the first step toward regaining control.

ScanLLM.ai was created to give teams that clarity. Because you can't manage what you can't see, and you can't scale what you don't understand.`
    },
    {
      id: 3,
      title: 'The Hidden Costs of AI Adoption Nobody Talks About',
      category: 'Cost Management',
      excerpt: 'Companies racing to adopt LLMs tend to focus on one number: token cost. But anyone who has worked inside a modern engineering organization knows that tokens are the least of your problems.',
      readTime: '5 min read',
      date: 'November 2025',
      featured: false,
      content: `Companies racing to adopt LLMs tend to focus on one number: token cost. It's visible, easy to benchmark, and simple to compare across models. But anyone who has worked inside a modern engineering organization knows that tokens are the least of your problems. The real costs — the ones that accumulate silently — come from the operational, architectural, and organizational complexity that AI introduces.

One hidden cost is integration drift. Teams move fast, prototypes become production code, and suddenly you have five services using five different SDK versions, wrappers, and retry patterns. Each integration adds a long-term maintenance tax that few teams acknowledge upfront.

Another cost is prompt maintenance. Prompts evolve as the product evolves, but without clear ownership or version control, they become stale. A prompt written by a developer last quarter can quietly degrade performance today, and nobody notices until customers do.

Then there's debugging time. LLMs are not deterministic systems. Small upstream changes — a model update, a parameter shift, a provider outage — can break workflows in ways that defy traditional debugging. Engineers spend hours chasing issues that originate in systems they don't control.

The fourth cost sits in data entanglement. LLMs often become embedded in sensitive workflows before teams have mapped out data boundaries. Understanding how data moves through prompts, embeddings, and pipelines becomes a compliance challenge that no audit trail was prepared for.

On top of that, API instability and model version churn mean teams must constantly update integrations. What seems like a one-line upgrade often ripples through tests, prompts, business logic, and downstream services.

The final hidden cost is migration complexity. Switching models or vendors sounds straightforward in theory. In practice, hidden dependencies emerge: outdated prompts, brittle RAG pipelines, divergent evaluation frameworks, and services you forgot were calling the old model. What should take days turns into weeks.

The truth is simple: the bill for AI adoption rarely matches the invoice from the model provider. The real costs are operational — and they grow in silence until an organization finally stops to measure them.`
    },
    {
      id: 4,
      title: 'A Practical Guide to Standardizing LLM Usage Across Your Organization',
      category: 'Best Practices',
      excerpt: 'As organizations accelerate LLM adoption, engineering teams face a common problem: every group uses AI differently.',
      readTime: '7 min read',
      date: 'November 2025',
      featured: false,
      content: `As organizations accelerate LLM adoption, engineering teams face a common problem: every group uses AI differently. Some build directly on OpenAI or Anthropic. Others depend on LangChain or custom wrappers. A few experiment with vLLM or Transformers on their own. What starts as healthy exploration becomes fragmentation that slows teams down.

Standardization is not about restricting innovation. It's about making sure every team benefits from the same guardrails, quality checks, and operational stability. The first step is creating a preferred stack — a clear recommendation for providers, SDKs, and model versions. When defaults exist, people use them.

Equally important is centralizing API access. A routing layer or gateway ensures consistent logging, safe handling of sensitive data, rate limiting, and cost tracking. Without this, you end up with dozens of services making direct and inconsistent LLM calls, creating a governance nightmare.

Prompts need structure too. Versioning prompts and storing them in a shared repository allows teams to track changes, roll back quickly, and maintain consistency. Prompts that live in scattered files, wikis, or Slack threads are impossible to manage long-term.

Clear ownership matters. Assigning responsibility for prompts, routing rules, safety checks, and evaluation frameworks prevents the "everyone owns it so no one owns it" problem.

To maintain quality, organizations need a shared evaluation harness that teams can plug into. This avoids the situation where every team invents its own testing strategy, making model upgrades unpredictable.

AI observability should be adopted early. Teams need to monitor latency, cost, error modes, drift, and token usage. Without this data, evolving an AI system becomes guesswork.

And before enforcing any of these standards, organizations must start with visibility — understanding where LLM usage already exists. You cannot enforce consistency until you know the terrain.

Standardization doesn't slow teams down. It creates alignment, reduces duplication, and gives engineering organizations the confidence to scale AI safely and systematically.`
    },
    {
      id: 5,
      title: 'What Platform Teams Should Monitor in AI Systems',
      category: 'Monitoring',
      excerpt: 'AI systems behave differently from traditional software. They\'re probabilistic, dependent on external providers, and influenced by data in ways that are not always transparent.',
      readTime: '6 min read',
      date: 'November 2025',
      featured: false,
      content: `AI systems behave differently from traditional software. They're probabilistic, dependent on external providers, and influenced by data, prompts, and model architecture in ways that are not always transparent. For platform teams, this means expanding the definition of what "monitoring" really means.

The first dimension is latency. Unlike traditional APIs, LLM latency can vary widely based on model load, provider conditions, prompt size, or even time of day. Small latency spikes can cascade into user-visible delays, especially in chat or real-time workflows.

Next is error behavior. AI failures are diverse: malformed responses, safety refusals, quota limits, provider timeouts, and model-specific quirks. Each failure type requires different handling, and ignoring them leads to brittle systems that break under pressure.

Platform teams must also track token consumption. Costs can grow quickly and silently, especially when prompts expand, input text balloons, or multiple teams reuse the same endpoint without monitoring.

Another area is prompt drift. Prompts evolve — intentionally or accidentally. Teams add small patches, update assumptions, or collaborate informally. Without monitoring how prompts change over time, organizations lose control over quality and reproducibility.

For companies using retrieval-augmented generation, RAG retrieval quality becomes a critical metric. Stale indexes, mismatched embedding models, and poorly tuned retrievers degrade output quality long before the model itself becomes a bottleneck.

Model routing is another important dimension. As organizations adopt multiple models, unexpected routing behavior can emerge — fallback mechanisms triggering too often, requests hitting the wrong model, or teams bypassing the intended gateway.

Finally, platform teams must understand cross-service dependencies. LLM usage hides inside microservices, jobs, and pipelines. Without a clear map of dependencies, routine updates can create outages that ripple across the system.

AI systems introduce new operational risks, and monitoring must evolve accordingly. Visibility into these behaviors is not optional — it's essential for building reliable, governed, and cost-efficient AI products.`
    }
  ];

  const [selectedCategory, setSelectedCategory] = useState('all');
  const featuredBlog = blogs.find(blog => blog.featured);
  const latestBlogs = blogs.filter(blog => !blog.featured);
  
  const categories = ['all', ...new Set(blogs.map(blog => blog.category))];
  
  // Filter all blogs (including featured) when category is selected
  const filteredBlogs = selectedCategory === 'all' 
    ? latestBlogs 
    : blogs.filter(blog => blog.category === selectedCategory);

  return (
    <div className="min-h-screen bg-zinc-950 py-16">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-zinc-100 mb-4 tracking-tight">
            ScanLLM Blog
          </h1>
          <p className="text-lg text-zinc-400">
            Insights on AI dependency management and engineering best practices
          </p>
        </div>

        {/* Featured Article */}
        {featuredBlog && (
          <div className="mb-16">
            <div className="bg-zinc-900 text-white rounded-2xl overflow-hidden border border-zinc-800">
              <div className="grid md:grid-cols-2 gap-0">
                {/* Left side - Featured label and title */}
                <div className="p-12 flex flex-col justify-center">
                  <Badge className="bg-indigo-600 text-white mb-6 w-fit">
                    FEATURED
                  </Badge>
                  <h2 className="text-4xl font-bold mb-4">
                    {featuredBlog.title}
                  </h2>
                  <p className="text-gray-400 text-lg">
                    {featuredBlog.category}
                  </p>
                </div>
                
                {/* Right side - Details */}
                <div className="bg-zinc-900 text-zinc-100 p-12 flex flex-col justify-center">
                  <Badge variant="outline" className="mb-4 w-fit border-zinc-600 text-zinc-300">
                    {featuredBlog.category}
                  </Badge>
                  <h3 className="text-2xl font-semibold mb-4">
                    {featuredBlog.title}
                  </h3>
                  <p className="text-zinc-400 mb-6">
                    {featuredBlog.excerpt}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-zinc-500 mb-6">
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {featuredBlog.date}
                    </span>
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {featuredBlog.readTime}
                    </span>
                  </div>
                  <button
                    onClick={() => navigate(`/blog/${featuredBlog.id}`)}
                    className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-500 transition-colors inline-flex items-center gap-2 w-fit"
                  >
                    READ ARTICLE
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Category Filter */}
        <div className="mb-8">
          <div className="flex gap-2 flex-wrap">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedCategory === cat
                    ? 'bg-indigo-600 text-white'
                    : 'bg-zinc-900 text-zinc-400 hover:bg-zinc-800 border border-zinc-700'
                }`}
              >
                {cat === 'all' ? 'All Articles' : cat}
              </button>
            ))}
          </div>
        </div>

        {/* Latest Articles Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-zinc-100">
            Latest Articles
          </h2>
        </div>

        {/* Articles Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredBlogs.map(blog => (
            <div
              key={blog.id}
              className="bg-zinc-900 rounded-xl border border-zinc-800 overflow-hidden hover:border-zinc-600 transition-colors cursor-pointer"
              onClick={() => navigate(`/blog/${blog.id}`)}
            >
              <div className="p-6">
                <Badge variant="secondary" className="mb-3 bg-zinc-800 text-zinc-300">
                  {blog.category}
                </Badge>
                <h3 className="text-xl font-semibold text-zinc-100 mb-3">
                  {blog.title}
                </h3>
                <p className="text-zinc-400 text-sm mb-4 line-clamp-3">
                  {blog.excerpt}
                </p>
                <div className="flex items-center gap-4 text-xs text-zinc-500">
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {blog.date}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {blog.readTime}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Blog;
