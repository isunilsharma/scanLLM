import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';
import { generateText, streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const client = new OpenAI();
const anthropic = new Anthropic();

async function chat() {
  const result = await generateText({
    model: openai('gpt-4o'),
    prompt: 'Hello',
  });
  return result;
}
