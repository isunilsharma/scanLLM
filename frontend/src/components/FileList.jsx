import React, { useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';

const FileList = ({ files }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-300';
      case 'medium': return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
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
          <span key={i} className="bg-yellow-200 font-semibold px-1 rounded">
            {parts[i]}
          </span>
        );
      }
    }
    
    return elements;
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <svg className="w-12 h-12 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            className="border border-slate-200 rounded-lg overflow-hidden"
          >
            <AccordionTrigger className="px-4 py-3 hover:bg-slate-50 hover:no-underline">
              <div className="flex items-center justify-between w-full pr-4">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex-shrink-0">
                    <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <span className="text-sm font-mono text-slate-900 truncate text-left">
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
                  <Badge className="bg-slate-900 text-white text-xs">
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
                    className="bg-slate-50 rounded-lg p-4 border border-slate-200"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          Line {occ.line_number}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          {occ.framework}
                        </Badge>
                      </div>
                      <span className="text-xs text-slate-500">{occ.pattern_name}</span>
                    </div>
                    <pre className="text-xs font-mono text-slate-900 bg-white rounded p-3 overflow-x-auto border border-slate-200">
                      {occ.line_text}
                    </pre>
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
