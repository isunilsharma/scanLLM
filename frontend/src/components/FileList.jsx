import React, { useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';

const FileList = ({ files }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'medium': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'low': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      default: return 'bg-zinc-800 text-zinc-200 border-zinc-700';
    }
  };

  const highlightSnippet = (snippet) => {
    if (!snippet) return null;
    
    // Replace [[[HIT]]]...[[[ENDHIT]]] with styled span
    const parts = snippet.split(/\[\[\[HIT\]\]\]|\[\[\[ENDHIT\]\]\]/);
    const elements = [];
    
    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 0) {
        // Normal text
        elements.push(<span key={i}>{parts[i]}</span>);
      } else {
        // Highlighted match
        elements.push(
          <span key={i} className="bg-yellow-500/30 font-semibold px-1 rounded">
            {parts[i]}
          </span>
        );
      }
    }
    
    return elements;
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-12 text-zinc-500">
        <svg className="w-12 h-12 mx-auto mb-4 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>No files found matching your criteria</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[600px] pr-4">
      <Accordion type="multiple" className="space-y-3" data-testid="file-list">
        {files.map((file, idx) => (
          <AccordionItem
            key={idx}
            value={`file-${idx}`}
            className="border border-zinc-800 rounded-lg overflow-hidden"
          >
            <AccordionTrigger className="px-4 py-3 hover:bg-zinc-800/30">
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-3 flex-1 min-w-0 pr-4">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span className="text-sm font-mono text-zinc-100 truncate text-left">
                    {file.file_path}
                  </span>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="flex gap-1">
                    {file.frameworks.slice(0, 2).map(fw => (
                      <Badge key={fw} variant="secondary" className="text-xs">
                        {fw}
                      </Badge>
                    ))}
                    {file.frameworks.length > 2 && (
                      <Badge variant="secondary" className="text-xs">
                        +{file.frameworks.length - 2}
                      </Badge>
                    )}
                  </div>
                  <Badge className="bg-zinc-900 text-white text-xs">
                    {file.occurrences.length}
                  </Badge>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 pb-4">
              <div className="space-y-3 pt-3">
                {file.occurrences.map((occ, occIdx) => (
                  <div
                    key={occIdx}
                    className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-800"
                  >
                    <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-xs">
                          Line {occ.line_number}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {occ.framework}
                        </Badge>
                        {occ.pattern_severity && (
                          <Badge className={`text-xs border ${getSeverityColor(occ.pattern_severity)}`}>
                            {occ.pattern_severity}
                          </Badge>
                        )}
                        {occ.pattern_category && (
                          <Badge variant="outline" className="text-xs">
                            {occ.pattern_category.replace(/_/g, ' ')}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-zinc-500">{occ.pattern_name}</span>
                    </div>
                    
                    {occ.pattern_description && (
                      <p className="text-xs text-zinc-400 mb-3 italic">{occ.pattern_description}</p>
                    )}
                    
                    {/* Code Snippet with highlighting */}
                    {occ.snippet ? (
                      <pre className="text-xs font-mono text-zinc-100 bg-zinc-900 rounded p-3 overflow-x-auto border border-zinc-700 whitespace-pre-wrap">
                        {highlightSnippet(occ.snippet)}
                      </pre>
                    ) : (
                      <pre className="text-xs font-mono text-zinc-100 bg-zinc-900 rounded p-3 overflow-x-auto border border-zinc-700">
                        {occ.line_text}
                      </pre>
                    )}
                    
                    {/* Contract metadata */}
                    {(occ.model_name || occ.temperature !== null || occ.max_tokens || occ.is_streaming || occ.has_tools) && (
                      <div className="bg-blue-500/10 rounded p-3 mt-3 text-xs">
                        <h5 className="font-semibold text-blue-300 mb-2">Detected Configuration</h5>
                        <div className="grid grid-cols-2 gap-2 text-blue-300">
                          {occ.model_name && (
                            <div>
                              <span className="text-blue-400">Model:</span> <span className="font-mono">{occ.model_name}</span>
                            </div>
                          )}
                          {occ.temperature !== null && (
                            <div>
                              <span className="text-blue-400">Temperature:</span> {occ.temperature}
                            </div>
                          )}
                          {occ.max_tokens && (
                            <div>
                              <span className="text-blue-400">Max Tokens:</span> {occ.max_tokens}
                            </div>
                          )}
                          {occ.is_streaming && (
                            <div>
                              <span className="text-blue-400">Streaming:</span> Yes
                            </div>
                          )}
                          {occ.has_tools && (
                            <div>
                              <span className="text-blue-400">Tools/Functions:</span> Yes
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Ownership info */}
                    {occ.owner_name && (
                      <div className="text-xs text-zinc-400 mt-2 flex items-center gap-4">
                        <span><span className="font-medium">Owner:</span> {occ.owner_name}</span>
                        {occ.owner_committed_at && (
                          <span><span className="font-medium">Last modified:</span> {new Date(occ.owner_committed_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </ScrollArea>
  );
};

export default FileList;
