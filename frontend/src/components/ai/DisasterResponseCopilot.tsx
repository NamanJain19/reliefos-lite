import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  queryAiCopilot,
  getAiHealth,
  getAiContextPreview,
  reviewAiAction,
  AIStructuredResponse,
  AIProposedAction,
  AIProviderHealth,
  ActionReviewResponse,
} from '../../services/api';
import { useLocationContext } from '../../context/LocationContext';

interface CopilotMessage {
  id: string;
  sender: 'operator' | 'copilot';
  timestamp: string;
  text?: string;
  structuredResponse?: AIStructuredResponse;
  isError?: boolean;
}

const SUGGESTED_PROMPTS = [
  {
    label: 'Highest Priority Flood Zones',
    icon: 'flood',
    query: 'Which flood-affected zones currently have the highest priority?',
  },
  {
    label: 'Inventory Shortages & Deficit',
    icon: 'inventory_2',
    query: 'Where is relief inventory insufficient?',
  },
  {
    label: 'Unmet Field Demands',
    icon: 'pending_actions',
    query: 'Which demands are still unmet?',
  },
  {
    label: 'Road Closure & Detour Impact',
    icon: 'alt_route',
    query: 'What is the impact of a road closure on available routes?',
  },
  {
    label: 'CP-SAT Optimizer Allocation',
    icon: 'calculate',
    query: 'What resource allocation has the optimizer recommended, and why?',
  },
  {
    label: 'Situation Delta (What Changed)',
    icon: 'history_toggle_off',
    query: 'What changed since the last recorded situation?',
  },
  {
    label: 'Operator Action Checklist',
    icon: 'checklist',
    query: 'What should an operator review next?',
  },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  initialQuery?: string;
}

export const DisasterResponseCopilot: React.FC<Props> = ({ isOpen, onClose, initialQuery }) => {
  const navigate = useNavigate();
  const { selectedLocation } = useLocationContext();
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [providerHealth, setProviderHealth] = useState<AIProviderHealth | null>(null);
  const [selectedZone, setSelectedZone] = useState<string>('');
  const [showContextPreview, setShowContextPreview] = useState(false);
  const [contextPreviewData, setContextPreviewData] = useState<any>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [officerName, setOfficerName] = useState('Insp. S. Sharma (EOC Planner)');
  const [actionStatuses, setActionStatuses] = useState<Record<string, { status: string; auditId?: string }>>({});
  const [actionNotes, setActionNotes] = useState<Record<string, string>>({});
  const [signingActionId, setSigningActionId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      loadHealth();
      if (messages.length === 0) {
        // Welcome intro message tailored to active operational sector
        const introText = selectedLocation.id === 'kamrup_metro'
          ? 'RELIEFOS Copilot ready. I synthesize verified operational context from ASDMA GIS layers, Brahmaputra river gauges, Sarusajai depot inventory, and Google OR-Tools CP-SAT optimizations. All guidance is strictly advisory decision support under ASDMA Form 8B officer review.'
          : `RELIEFOS Copilot ready for ${selectedLocation.displayName}. Monitoring verified CWC hydrology along ${selectedLocation.primaryRiver}. Note: Local depots are unconfigured for this district; logistics are coordinated via Central Staging Depot in Guwahati. All guidance is strictly advisory decision support under ASDMA Form 8B officer review.`;
        setMessages([
          {
            id: 'welcome-01',
            sender: 'copilot',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            text: introText,
          },
        ]);
      }
      if (initialQuery) {
        handleSendQuery(initialQuery);
      }
    }
  }, [isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const loadHealth = async () => {
    try {
      const res = await getAiHealth();
      setProviderHealth(res.data);
    } catch {
      setProviderHealth(null);
    }
  };

  const handleFetchContextPreview = async () => {
    setContextLoading(true);
    try {
      const res = await getAiContextPreview(undefined, selectedZone || undefined);
      setContextPreviewData(res.data);
      setShowContextPreview(true);
    } catch (err) {
      console.error('Failed to preview context', err);
    } finally {
      setContextLoading(false);
    }
  };

  const handleSendQuery = async (queryToSend?: string) => {
    const query = (queryToSend || inputText).trim();
    if (!query || isLoading) return;

    const userMessage: CopilotMessage = {
      id: `msg-${Date.now()}`,
      sender: 'operator',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!queryToSend) setInputText('');
    setIsLoading(true);

    try {
      const formattedQuery = selectedLocation.id === 'kamrup_metro'
        ? query
        : `[Active District: ${selectedLocation.displayName}] ${query}`;

      const response = await queryAiCopilot({
        query: formattedQuery,
        zone_code: selectedZone || (selectedLocation.id !== 'kamrup_metro' ? selectedLocation.shortName : undefined),
        operator_name: officerName,
      });

      const structured = response.data;
      const copilotMessage: CopilotMessage = {
        id: `resp-${Date.now()}`,
        sender: 'copilot',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        structuredResponse: structured,
      };

      setMessages((prev) => [...prev, copilotMessage]);
      loadHealth(); // refresh usage load
    } catch (err: any) {
      const errorDetail = err?.response?.data?.detail || err?.message || 'Emergency Copilot service encountered a network error.';
      const errorMessage: CopilotMessage = {
        id: `err-${Date.now()}`,
        sender: 'copilot',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: `Error: ${errorDetail}`,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReviewAction = async (action: AIProposedAction, decision: 'APPROVED' | 'REJECTED') => {
    setSigningActionId(action.action_id);
    try {
      const note = actionNotes[action.action_id] || (decision === 'APPROVED' ? 'Approved by watch officer under ASDMA Form 8B.' : 'Rejected by watch officer.');
      const res = await reviewAiAction({
        action_id: action.action_id,
        decision,
        officer_name: officerName,
        notes: note,
      });

      if (res.data && res.data.success) {
        setActionStatuses((prev) => ({
          ...prev,
          [action.action_id]: {
            status: res.data.status,
            auditId: res.data.audit_id,
          },
        }));
      }
    } catch (err) {
      console.error('Failed to review action', err);
      alert('Failed to record action review into database audit trail.');
    } finally {
      setSigningActionId(null);
    }
  };

  const getProvenanceBadge = (prov: string) => {
    switch (prov) {
      case 'LIVE':
        return 'bg-primary/10 text-primary border-primary/30';
      case 'MANUAL':
        return 'bg-secondary/10 text-secondary border-secondary/30';
      case 'LAST_KNOWN':
        return 'bg-tertiary/10 text-tertiary border-tertiary/30';
      case 'ESTIMATED':
        return 'bg-purple-400/10 text-purple-300 border-purple-400/30';
      case 'SIMULATED':
        return 'bg-cyan-400/10 text-cyan-300 border-cyan-400/30';
      default:
        return 'bg-error/10 text-error border-error/30';
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[1200] flex justify-end bg-black/60 backdrop-blur-sm transition-opacity animate-fadeIn"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="RELIEFOS AI Copilot Drawer"
    >
      {/* Drawer Container */}
      <div
        className="w-full max-w-2xl bg-[#0e1d2c] border-l border-outline-variant/40 flex flex-col h-full shadow-2xl relative z-[1201] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Top Header */}
        <div className="p-4 border-b border-outline-variant/30 bg-[#122130] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-[22px]">smart_toy</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-headline-sm text-[15px] font-bold text-on-surface">
                  RELIEFOS AI Copilot
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono-data font-bold bg-primary/15 text-primary border border-primary/30">
                  DECISION SUPPORT
                </span>
              </div>
              <p className="text-[11px] text-on-surface-variant">
                Grounded EOC Assistant • Zero Hallucination • Form 8B Human-in-the-Loop
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleFetchContextPreview}
              disabled={contextLoading}
              className="px-2.5 py-1 text-[11px] font-medium rounded border border-outline-variant hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors flex items-center gap-1.5 cursor-pointer"
              title="Inspect Live Operational Telemetry Context Bundle"
            >
              <span className="material-symbols-outlined text-[15px]">database</span>
              <span>Context</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
              aria-label="Close Copilot Drawer"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>

        {/* Telemetry Status Strip */}
        <div className="bg-[#010f1e] px-4 py-2 border-b border-outline-variant/20 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono-data shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${providerHealth?.provider_status === 'LIVE' ? 'bg-primary animate-pulse' : (providerHealth?.provider_status === 'ERROR' ? 'bg-error animate-ping' : 'bg-[#f5b84b]')}`}></span>
              <span className="text-outline">Engine:</span>
              <span className="text-on-surface font-semibold">
                {providerHealth ? `${providerHealth.effective_provider.toUpperCase()} (${providerHealth.model})` : 'DETERMINISTIC CORE'}
              </span>
              <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                providerHealth?.provider_status === 'LIVE'
                  ? 'bg-primary/20 text-primary border border-primary/40'
                  : providerHealth?.provider_status === 'ERROR'
                  ? 'bg-error/20 text-error border border-error/40'
                  : 'bg-[#f5b84b]/20 text-[#f5b84b] border border-[#f5b84b]/40'
              }`}>
                {providerHealth?.provider_status || 'MOCK'}
              </span>
            </div>
            <div className="hidden sm:flex items-center gap-1 text-on-surface-variant">
              <span>Circuit:</span>
              <span className={`font-bold ${providerHealth?.circuit_breaker_status === 'CLOSED' ? 'text-primary' : 'text-error'}`}>
                {providerHealth?.circuit_breaker_status || 'CLOSED'}
              </span>
            </div>
          </div>

          {/* Active Location Context Indicator */}
          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container border border-outline-variant/30 text-[10px]">
            <span className="material-symbols-outlined text-[13px] text-secondary">location_on</span>
            <span className="text-secondary font-bold">{selectedLocation.shortName}</span>
            <span className="text-outline">({selectedLocation.tierBadgeText})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-outline">Target Sector:</span>
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="bg-surface-container border border-outline-variant/40 rounded px-2 py-0.5 text-[11px] text-on-surface focus:outline-none focus:border-primary"
            >
              <option value="">All Zones (Citywide)</option>
              <option value="ZONE 01">Zone 01 - North Guwahati</option>
              <option value="ZONE 02">Zone 02 - Bharalumukh</option>
              <option value="ZONE 03">Zone 03 - Dispur Capital</option>
              <option value="ZONE 04">Zone 04 - Pandu Ghat</option>
              <option value="ZONE 05">Zone 05 - Noonmati</option>
            </select>
          </div>
        </div>

        {/* Suggested Quick Questions Scrollable Strip */}
        <div className="px-4 py-2 bg-[#0e1d2c] border-b border-outline-variant/20 overflow-x-auto flex items-center gap-2 no-scrollbar shrink-0">
          <span className="text-[10px] font-bold uppercase tracking-wider text-outline whitespace-nowrap">
            Tactical Inquiries:
          </span>
          {SUGGESTED_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSendQuery(p.query)}
              disabled={isLoading}
              className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-surface-container hover:bg-primary/15 hover:border-primary/40 border border-outline-variant/40 text-on-surface-variant hover:text-on-surface transition-all whitespace-nowrap flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[13px] text-primary">{p.icon}</span>
              <span>{p.label}</span>
            </button>
          ))}
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#051423]">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.sender === 'operator' ? 'items-end' : 'items-start'}`}>
              
              {/* Header Label */}
              <div className="flex items-center gap-2 mb-1 px-1">
                <span className="text-[10px] font-mono-data font-bold uppercase tracking-wider text-outline">
                  {msg.sender === 'operator' ? officerName : 'ASDMA RELIEFOS COPILOT'}
                </span>
                <span className="text-[10px] text-outline">{msg.timestamp}</span>
              </div>

              {/* Message Bubble */}
              {msg.sender === 'operator' ? (
                <div className="max-w-[85%] bg-primary/15 border border-primary/30 text-on-surface px-4 py-3 rounded-2xl rounded-tr-none text-[13px] leading-relaxed shadow-sm">
                  {msg.text}
                </div>
              ) : msg.isError ? (
                <div className="max-w-[90%] bg-error/10 border border-error/40 text-error px-4 py-3 rounded-2xl rounded-tl-none text-[12px] flex items-start gap-2 shadow-sm">
                  <span className="material-symbols-outlined text-[18px] shrink-0 mt-0.5">error</span>
                  <div>{msg.text}</div>
                </div>
              ) : msg.structuredResponse ? (
                <div className="w-full bg-surface-container border border-outline-variant/40 rounded-2xl rounded-tl-none p-4 space-y-4 shadow-md text-on-surface">
                  
                  {/* Non-Autonomous Advisory Badge */}
                  <div className="flex items-center justify-between pb-2 border-b border-outline-variant/25">
                    <div className="flex items-center gap-1.5 text-primary text-[11px] font-bold tracking-wide">
                      <span className="material-symbols-outlined text-[16px]">verified</span>
                      <span>AI DECISION SUPPORT • NON-AUTONOMOUS</span>
                    </div>
                    <span className="text-[10px] font-mono-data px-2 py-0.5 rounded bg-surface-container-high text-outline border border-outline-variant/20">
                      Audit: {msg.structuredResponse.audit_id}
                    </span>
                  </div>

                  {/* Provider Inference Transparency Disclosure */}
                  {msg.structuredResponse.is_mock_fallback || msg.structuredResponse.execution_mode?.includes('MOCK') ? (
                    <div className="bg-[#f5b84b]/10 border border-[#f5b84b]/40 text-[#f5b84b] px-3 py-1.5 rounded-lg text-[11px] font-mono-data flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[15px]">info</span>
                        <span className="font-bold">MOCK FALLBACK DISCLOSURE:</span>
                        <span>Operating on verified deterministic ground rules.</span>
                      </div>
                      {msg.structuredResponse.fallback_reason && (
                        <span className="text-[10px] text-outline truncate max-w-xs" title={msg.structuredResponse.fallback_reason}>
                          {msg.structuredResponse.fallback_reason}
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="bg-primary/10 border border-primary/40 text-primary px-3 py-1.5 rounded-lg text-[11px] font-mono-data flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                        <span className="font-bold">LIVE CLOUD INFERENCE:</span>
                        <span>{msg.structuredResponse.provider_used.toUpperCase()} ({msg.structuredResponse.model_used})</span>
                      </div>
                      <span className="text-[10px] font-bold text-primary">GROUNDED CONTEXT VERIFIED</span>
                    </div>
                  )}

                  {/* 1. Tactical Recommendation */}
                  <div className="bg-primary/10 border border-primary/30 p-3.5 rounded-xl">
                    <div className="text-[11px] font-bold text-primary uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[15px]">recommend</span>
                      Tactical Recommendation
                    </div>
                    <div className="text-[13px] font-semibold text-on-surface leading-snug">
                      {msg.structuredResponse.recommendation}
                    </div>
                  </div>

                  {/* 2. Detailed Rationale & Constraints */}
                  <div>
                    <div className="text-[11px] font-bold uppercase tracking-wider text-outline mb-1.5 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[15px]">psychology</span>
                      Operational Rationale & Solver Analysis
                    </div>
                    <p className="text-[12px] text-on-surface-variant leading-relaxed">
                      {msg.structuredResponse.detailed_explanation}
                    </p>
                  </div>

                  {/* 3. Supporting Evidence Matrix */}
                  {msg.structuredResponse.supporting_evidence.length > 0 && (
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-outline mb-2 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[15px]">fact_check</span>
                        Verified Supporting Telemetry & Citations
                      </div>
                      <div className="grid grid-cols-1 gap-2">
                        {msg.structuredResponse.supporting_evidence.map((ev, i) => (
                          <div
                            key={i}
                            className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-2.5 text-[11px] flex flex-col gap-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-on-surface text-[12px]">{ev.source}</span>
                              <span className={`px-2 py-0.5 rounded text-[9px] font-mono-data font-bold border ${getProvenanceBadge(ev.provenance_state)}`}>
                                {ev.provenance_state}
                              </span>
                            </div>
                            <div className="text-on-surface-variant font-mono-data text-[11px]">{ev.data_point}</div>
                            <div className="text-[10px] text-outline flex items-center justify-between pt-0.5">
                              <span>Observed: {ev.observation_time}</span>
                              <span>Tier: {ev.trust_tier}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 4. Proposed Reviewable Actions (Form 8B Sign-Off) */}
                  {msg.structuredResponse.proposed_actions && msg.structuredResponse.proposed_actions.length > 0 && (
                    <div className="pt-2 border-t border-outline-variant/20">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-tertiary mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className="material-symbols-outlined text-[16px]">draw</span>
                          Reviewable Actions (Statutory Human Sign-Off Required)
                        </div>
                        <span className="text-[10px] text-outline">ASDMA Form 8B</span>
                      </div>

                      <div className="space-y-2.5">
                        {msg.structuredResponse.proposed_actions.map((act) => {
                          const actionReviewState = actionStatuses[act.action_id];
                          const isSigning = signingActionId === act.action_id;

                          return (
                            <div
                              key={act.action_id}
                              className="bg-surface-container-lowest/90 border border-outline-variant/40 rounded-xl p-3 flex flex-col gap-2 relative overflow-hidden"
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono-data text-[10px] px-1.5 py-0.5 rounded bg-surface-container text-outline border border-outline-variant/30">
                                      {act.action_id}
                                    </span>
                                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                      act.priority === 'CRITICAL' ? 'bg-error/20 text-error' : 'bg-tertiary/20 text-tertiary'
                                    }`}>
                                      {act.priority}
                                    </span>
                                    <span className="text-[10px] font-mono-data text-outline">
                                      Target: {act.target_entity}
                                    </span>
                                  </div>
                                  <h4 className="font-semibold text-[13px] text-on-surface mt-1">{act.title}</h4>
                                </div>
                              </div>

                              <p className="text-[11px] text-on-surface-variant leading-snug">
                                {act.rationale}
                              </p>

                              {/* Review Controls or Approved State */}
                              {actionReviewState ? (
                                <div className={`p-2 rounded-lg text-[11px] font-medium flex items-center justify-between border ${
                                  actionReviewState.status === 'ACTION_APPROVED'
                                    ? 'bg-primary/10 border-primary/30 text-primary'
                                    : 'bg-error/10 border-error/30 text-error'
                                }`}>
                                  <div className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-[16px]">
                                      {actionReviewState.status === 'ACTION_APPROVED' ? 'check_circle' : 'cancel'}
                                    </span>
                                    <span>
                                      {actionReviewState.status === 'ACTION_APPROVED'
                                        ? `Officially Approved by ${officerName}`
                                        : `Proposal Rejected by ${officerName}`}
                                    </span>
                                  </div>
                                  {actionReviewState.auditId && (
                                    <span className="font-mono-data text-[10px] opacity-80">
                                      {actionReviewState.auditId}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <div className="pt-1 flex items-center justify-between gap-2">
                                  <div className="flex items-center gap-2">
                                    <button
                                      type="button"
                                      onClick={() => handleReviewAction(act, 'APPROVED')}
                                      disabled={isSigning}
                                      className="px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-on-primary text-[11px] font-bold flex items-center gap-1.5 cursor-pointer shadow-sm transition-all disabled:opacity-50"
                                      title="Sign and authorize this operational action according to ASDMA Form 8B"
                                    >
                                      <span className="material-symbols-outlined text-[15px]">edit_document</span>
                                      <span>{isSigning ? 'Signing...' : 'Review & Sign'}</span>
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleReviewAction(act, 'REJECTED')}
                                      disabled={isSigning}
                                      className="px-2.5 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container text-on-surface-variant hover:text-on-surface text-[11px] font-medium cursor-pointer transition-colors"
                                      title="Dismiss or reject recommendation"
                                    >
                                      Dismiss
                                    </button>
                                  </div>

                                  {act.suggested_route && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        onClose();
                                        navigate(act.suggested_route!);
                                      }}
                                      className="text-primary hover:text-primary-fixed text-[11px] font-medium flex items-center gap-1 cursor-pointer transition-colors"
                                    >
                                      <span>Go to Screen</span>
                                      <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* 5. Identified Operational Risks */}
                  {msg.structuredResponse.identified_risks_and_limitations.length > 0 && (
                    <div className="bg-surface-container-lowest/60 border border-outline-variant/20 rounded-xl p-3">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-[#F5B84B] mb-1.5 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[15px]">warning</span>
                        Operational Risks & Roadway Limitations
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-[11px] text-on-surface-variant">
                        {msg.structuredResponse.identified_risks_and_limitations.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 6. Stale or Missing Data Disclosures */}
                  {msg.structuredResponse.missing_or_stale_data_disclosures.length > 0 && (
                    <div className="bg-surface-container-lowest/40 border border-outline-variant/20 rounded-xl p-3">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-outline mb-1.5 flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[15px]">info</span>
                        Data Freshness & Provenance Disclosures
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-[11px] text-outline">
                        {msg.structuredResponse.missing_or_stale_data_disclosures.map((d, i) => (
                          <li key={i}>{d}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Statutory Footer */}
                  <div className="text-[10px] text-outline text-center pt-2 border-t border-outline-variant/20">
                    {msg.structuredResponse.statutory_compliance_notice}
                  </div>

                </div>
              ) : (
                <div className="max-w-[85%] bg-surface-container border border-outline-variant/40 text-on-surface px-4 py-3 rounded-2xl rounded-tl-none text-[13px] leading-relaxed shadow-sm">
                  {msg.text}
                </div>
              )}
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex flex-col items-start space-y-2">
              <div className="flex items-center gap-2 px-1 text-[10px] font-mono-data font-bold uppercase tracking-wider text-outline">
                <span>ASDMA RELIEFOS COPILOT</span>
                <span>PROCESSING</span>
              </div>
              <div className="bg-surface-container border border-outline-variant/40 rounded-2xl rounded-tl-none p-4 flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <div className="text-[12px] text-on-surface-variant">
                  Compiling operational context, running CP-SAT constraints, and formulating grounded decision support...
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-outline-variant/30 bg-[#0e1d2c] shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendQuery();
            }}
            className="flex items-center gap-2"
          >
            <div className="flex-1 relative">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Ask about highest priority zones, inventory shortages, unmet demands, detours, or CP-SAT recommendations..."
                disabled={isLoading}
                className="w-full bg-surface-container-high border border-outline-variant/40 rounded-xl px-4 py-3 text-[13px] text-on-surface placeholder:text-outline focus:outline-none focus:border-primary pr-10"
              />
              {inputText && (
                <button
                  type="button"
                  onClick={() => setInputText('')}
                  className="absolute right-3 top-3 text-outline hover:text-on-surface"
                >
                  <span className="material-symbols-outlined text-[18px]">clear</span>
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="p-3 rounded-xl bg-primary hover:bg-primary/90 text-on-primary font-bold flex items-center justify-center cursor-pointer transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
              title="Submit Operational Inquiry"
            >
              <span className="material-symbols-outlined text-[20px]">send</span>
            </button>
          </form>

          {/* Operator Footer Status */}
          <div className="mt-2 flex items-center justify-between text-[11px] text-outline">
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[14px] text-secondary">badge</span>
              <span>Officer on duty: <strong className="text-on-surface-variant">{officerName}</strong></span>
            </div>
            <div className="hidden sm:flex items-center gap-1">
              <span>Press Enter to send • Verified Data Grounding Only</span>
            </div>
          </div>
        </div>

      </div>

      {/* Context Preview Modal */}
      {showContextPreview && contextPreviewData && (
        <div
          className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn"
          onClick={() => setShowContextPreview(false)}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="w-full max-w-3xl bg-[#122130] border border-outline-variant/50 rounded-2xl p-6 shadow-2xl flex flex-col max-h-[85vh] relative z-[1301] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[22px]">fact_check</span>
                <h3 className="font-headline-sm text-[16px] font-bold text-on-surface">
                  Live Operational Context Inspector
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowContextPreview(false)}
                className="p-1 rounded-lg hover:bg-surface-container-high text-on-surface-variant"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>

            <div className="my-3 flex items-center justify-between text-[12px] font-mono-data bg-surface-container-low p-2.5 rounded-lg border border-outline-variant/20">
              <div>System Mode: <strong className="text-primary">{contextPreviewData.system_mode}</strong></div>
              <div>Compiled Domains: <strong className="text-on-surface">{contextPreviewData.total_domains_compiled}</strong></div>
              <div>Compiled At: <span className="text-outline">{contextPreviewData.compiled_at}</span></div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {contextPreviewData.context_items.map((item: any, idx: number) => (
                <div key={idx} className="bg-surface-container-low border border-outline-variant/30 rounded-xl p-3 text-[12px]">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-on-surface text-[13px]">{item.title}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono-data font-bold border ${getProvenanceBadge(item.provenance_state)}`}>
                      {item.provenance_state}
                    </span>
                  </div>
                  <div className="text-outline text-[11px] mb-2">Agency: {item.source_agency} • Freshness: {item.observation_time}</div>
                  <p className="text-on-surface-variant font-mono-data text-[11px] bg-surface-container-lowest p-2 rounded border border-outline-variant/20">
                    {item.summary}
                  </p>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-outline-variant/30 flex justify-end">
              <button
                type="button"
                onClick={() => setShowContextPreview(false)}
                className="px-4 py-2 rounded-xl bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-[12px] font-semibold transition-colors cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
