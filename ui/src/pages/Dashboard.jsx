import { useState, useEffect, useCallback } from 'react';
import api from '../api/client';
import { shortId, isJobRunning } from '../utils/helpers';
import { Topbar, LogsPanel } from '../components/layout';
import { EmptyState, LoadingSpinner } from '../components/common';
import { PipelineColumn, EndpointCard, AttackCard, ScoreCard, GuardrailCard } from '../components/pipeline';
import { FormModal, DetailPanel, ReportModal, AttackRecordsModal, GuardrailsModal, JudgesModal, GeneratorsModal, MatricesModal } from '../components/modals';
import { useTour } from '../components/tour';

export const Dashboard = () => {
  const { hasCompletedTour, startTour, isActive: tourActive } = useTour();

  // Data state
  const [endpoints, setEndpoints] = useState([]);
  const [attacks, setAttacks] = useState([]);
  const [scores, setScores] = useState([]);
  const [guardrails, setGuardrails] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [matrices, setMatrices] = useState([]);
  const [loading, setLoading] = useState({ endpoints: true, attacks: true, scores: true, guardrails: true });
  const [error, setError] = useState({});

  // Selection state
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [selectedAttack, setSelectedAttack] = useState(null);
  const [selectedScore, setSelectedScore] = useState(null);
  const [selectedGuardrail, setSelectedGuardrail] = useState(null);

  // UI state
  const [detailPanel, setDetailPanel] = useState({ item: null, type: null });
  const [panelCollapsed, setPanelCollapsed] = useState(false);
  const [reportModal, setReportModal] = useState(null);
  const [attackRecordsModal, setAttackRecordsModal] = useState(null);
  const [guardrailsModal, setGuardrailsModal] = useState(null);
  const [formModal, setFormModal] = useState(null);
  const [formLoading, setFormLoading] = useState(false);
  const [showJudgesModal, setShowJudgesModal] = useState(false);
  const [showGeneratorsModal, setShowGeneratorsModal] = useState(false);
  const [showMatricesModal, setShowMatricesModal] = useState(false);

  // Check if any jobs are running (for polling)
  const hasRunningJobs = [...attacks, ...scores, ...guardrails].some(isJobRunning);

  // Fetch functions
  const fetchEndpoints = useCallback(() => {
    api.getEndpoints()
      .then(data => { setEndpoints(Array.isArray(data) ? data : []); setError(e => ({ ...e, endpoints: null })); })
      .catch(err => setError(e => ({ ...e, endpoints: err.message })))
      .finally(() => setLoading(l => ({ ...l, endpoints: false })));
  }, []);

  const fetchAttacks = useCallback(() => {
    api.getAttacks()
      .then(data => { setAttacks(Array.isArray(data) ? data : []); setError(e => ({ ...e, attacks: null })); })
      .catch(err => setError(e => ({ ...e, attacks: err.message })))
      .finally(() => setLoading(l => ({ ...l, attacks: false })));
  }, []);

  const fetchScores = useCallback(() => {
    api.getScores()
      .then(data => { setScores(Array.isArray(data) ? data : []); setError(e => ({ ...e, scores: null })); })
      .catch(err => setError(e => ({ ...e, scores: err.message })))
      .finally(() => setLoading(l => ({ ...l, scores: false })));
  }, []);

  const fetchGuardrails = useCallback(() => {
    api.getGuardrails()
      .then(data => { setGuardrails(Array.isArray(data) ? data : []); setError(e => ({ ...e, guardrails: null })); })
      .catch(err => setError(e => ({ ...e, guardrails: err.message })))
      .finally(() => setLoading(l => ({ ...l, guardrails: false })));
  }, []);

  const fetchDatasets = useCallback(() => {
    api.getDatasets().then(data => setDatasets(Array.isArray(data) ? data : [])).catch(console.error);
  }, []);

  const fetchMatrices = useCallback(() => {
    api.getMatrices().then(data => setMatrices(Array.isArray(data) ? data : [])).catch(console.error);
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchEndpoints();
    fetchAttacks();
    fetchScores();
    fetchGuardrails();
    fetchDatasets();
    fetchMatrices();
  }, []);

  // Polling for running jobs (5 second interval to reduce API load)
  useEffect(() => {
    if (hasRunningJobs) {
      const interval = setInterval(() => {
        fetchAttacks();
        fetchScores();
        fetchGuardrails();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [hasRunningJobs, fetchAttacks, fetchScores, fetchGuardrails]);

  // Auto-start tour for first-time users with no data
  useEffect(() => {
    if (!loading.endpoints && endpoints.length === 0 && !hasCompletedTour && !tourActive) {
      // Small delay to let the UI settle
      const timeout = setTimeout(startTour, 500);
      return () => clearTimeout(timeout);
    }
  }, [loading.endpoints, endpoints.length, hasCompletedTour, tourActive, startTour]);

  // Filter data based on selections
  const filteredAttacks = selectedEndpoint
    ? attacks.filter(a => a.endpoint_id === selectedEndpoint.id)
    : attacks;

  const filteredScores = selectedAttack
    ? scores.filter(s => s.attack_id === selectedAttack.id)
    : scores;

  const filteredGuardrails = selectedScore
    ? guardrails.filter(g => g.score_id === selectedScore.id)
    : guardrails;

  // Handlers
  const handleCardClick = (item, type) => {
    setDetailPanel({ item, type });
    switch (type) {
      case 'endpoint':
        setSelectedEndpoint(selectedEndpoint?.id === item.id ? null : item);
        setSelectedAttack(null);
        setSelectedScore(null);
        setSelectedGuardrail(null);
        break;
      case 'attack':
        setSelectedAttack(selectedAttack?.id === item.id ? null : item);
        setSelectedScore(null);
        setSelectedGuardrail(null);
        break;
      case 'score':
        setSelectedScore(selectedScore?.id === item.id ? null : item);
        setSelectedGuardrail(null);
        break;
      case 'guardrail':
        setSelectedGuardrail(selectedGuardrail?.id === item.id ? null : item);
        break;
    }
  };

  const handleFormSubmit = async (values) => {
    setFormLoading(true);
    try {
      switch (formModal.type) {
        case 'endpoint':
          await api.createEndpoint({ name: values.name, type: values.type, base_url: values.url });
          fetchEndpoints();
          break;
        case 'attack':
          await api.createAttack({ endpoint: values.endpoint, dataset: values.dataset });
          fetchAttacks();
          break;
        case 'score':
          await api.createScore({
            attack_id: values.attack_id,
            age: values.age || 'child',
            matrix: values.matrix || 'educational'
          });
          fetchScores();
          break;
        case 'guardrail':
          await api.createGuardrail({
            score_id: values.score_id,
            max_rules: values.max_rules ? parseInt(values.max_rules) : 3,
            max_total: values.max_total ? parseInt(values.max_total) : 20
          });
          fetchGuardrails();
          break;
      }
      setFormModal(null);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setFormLoading(false);
    }
  };

  const openReport = (score) => setReportModal(score);
  const openAttackRecords = (attack) => setAttackRecordsModal(attack);
  const openGuardrails = (guardrail) => setGuardrailsModal(guardrail);

  const refreshAll = () => {
    fetchEndpoints();
    fetchAttacks();
    fetchScores();
    fetchGuardrails();
  };

  // Form configurations
  const formConfigs = {
    endpoint: {
      title: 'Add Endpoint',
      fields: [
        { name: 'name', label: 'Name', placeholder: 'my-chatbot', required: true },
        { name: 'type', label: 'Type', type: 'select', required: true, options: [
          { value: 'simple', label: 'Simple HTTP' },
          { value: 'openai', label: 'OpenAI Compatible' },
        ]},
        { name: 'url', label: 'URL', placeholder: 'http://localhost:8080/chat', required: true },
      ]
    },
    attack: {
      title: 'New Attack',
      fields: [
        { name: 'endpoint', label: 'Endpoint', type: 'select', required: true, options: endpoints.map(e => ({ value: e.name, label: e.name })) },
        { name: 'dataset', label: 'Dataset', type: 'select', required: true, options: datasets.map(d => ({ value: d.name, label: `${d.name} (${d.prompt_count || 0} prompts)` })), helpLink: { text: 'View prompts', urlTemplate: '/datasets?dataset={value}' } },
      ]
    },
    score: {
      title: 'New Score',
      fields: [
        { name: 'attack_id', label: 'Attack', type: 'select', required: true, options: attacks.filter(a => a.status === 'completed').map(a => ({ value: a.id, label: `${shortId(a.id)} - ${a.dataset_name}` })) },
        { name: 'age', label: 'Age Group', type: 'select', required: true, options: [
          { value: 'child', label: 'Child (6-12)' },
          { value: 'teenager', label: 'Teenager (13-17)' },
          { value: 'young_adult', label: 'Young Adult (18-25)' },
        ]},
        { name: 'matrix', label: 'Context', type: 'select', required: true, options: matrices.filter(m => m.name !== 'flat').map(m => ({ value: m.name, label: m.is_builtin ? `${m.name.charAt(0).toUpperCase() + m.name.slice(1)}` : m.name })) },
      ]
    },
    guardrail: {
      title: 'Generate Guardrails',
      fields: [
        { name: 'score_id', label: 'Score', type: 'select', required: true, options: scores.filter(s => s.status === 'completed').map(s => ({ value: s.id, label: `${shortId(s.id)} - ${s.final_score?.toFixed(1)}/5.0` })) },
        { name: 'max_rules', label: 'Max Rules per Criterion', type: 'number', required: false, placeholder: '3' },
        { name: 'max_total', label: 'Max Total Rules', type: 'number', required: false, placeholder: '20' },
      ]
    },
  };

  const panelWidth = panelCollapsed ? 48 : 420;
  const showPanel = detailPanel.item !== null;

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Topbar
        onJudgesClick={() => setShowJudgesModal(true)}
        onGeneratorsClick={() => setShowGeneratorsModal(true)}
        onMatricesClick={() => setShowMatricesModal(true)}
      />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}
      {showGeneratorsModal && <GeneratorsModal onClose={() => setShowGeneratorsModal(false)} />}
      {showMatricesModal && <MatricesModal onClose={() => setShowMatricesModal(false)} />}

      <div className="flex-1 flex overflow-hidden">
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden" style={{ marginRight: showPanel ? panelWidth : 0 }}>
          {/* Top section - 70% */}
          <div className="h-[70%] p-6 flex flex-col">
            {/* Main Layout */}
            <div className="flex flex-col gap-3 flex-1 min-h-0 overflow-hidden">
              {/* Flow Stepper */}
              <div className="flex items-center flex-shrink-0">
                {[
                  { name: 'Endpoints', subtitle: null },
                  { name: 'Attacks', subtitle: selectedEndpoint?.name },
                  { name: 'Scores', subtitle: selectedAttack ? shortId(selectedAttack.id) : null },
                  { name: 'Guardrails', subtitle: selectedScore ? shortId(selectedScore.id) : null },
                ].map((step, i, arr) => (
                  <div key={step.name} className="flex items-center gap-3 flex-1">
                    <div className="w-7 h-7 rounded-full bg-everyone-blue flex items-center justify-center flex-shrink-0 shadow-sm">
                      <span className="text-sm text-white font-bold">{i + 1}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-700">{step.name}</span>
                    {step.subtitle && (
                      <span className="text-xs text-everyone-blue truncate max-w-[100px]">for {step.subtitle}</span>
                    )}
                    {i < arr.length - 1 && (
                      <div className="flex-1 h-0.5 bg-gradient-to-r from-everyone-blue/50 to-everyone-blue/10 ml-2 rounded-full" />
                    )}
                  </div>
                ))}
              </div>

              {/* Pipeline Columns */}
              <div className="grid gap-6 flex-1 grid-cols-4 overflow-hidden">
                <PipelineColumn
                  tourId="endpoints"
                  addLabel="Add Endpoint"
                  onAdd={() => setFormModal({ type: 'endpoint' })}
                  description="AI chatbots, assistants or raw models you want to test. Connect any OpenAI-compatible API or simple HTTP endpoint."
                  loading={loading.endpoints}
                  error={error.endpoints}
                >
                  {endpoints.length === 0 ? <EmptyState message="No endpoints yet" /> :
                    endpoints.map(endpoint => (
                      <EndpointCard key={endpoint.id} endpoint={endpoint} selected={selectedEndpoint?.id === endpoint.id} onClick={() => handleCardClick(endpoint, 'endpoint')} onNewAttack={(ep) => setFormModal({ type: 'attack', initialValues: { endpoint: ep.name } })} />
                    ))
                  }
                </PipelineColumn>

                <PipelineColumn
                  tourId="attacks"
                  addLabel="New Attack"
                  onAdd={() => setFormModal({ type: 'attack' })}
                  description="Send adversarial prompts to test how an endpoint responds to challenging scenarios designed to probe safety boundaries."
                  loading={loading.attacks}
                  error={error.attacks}
                >
                  {filteredAttacks.length === 0 ? <EmptyState message="No attacks yet" /> :
                    filteredAttacks.map(attack => (
                      <AttackCard key={attack.id} attack={attack} selected={selectedAttack?.id === attack.id} onClick={() => handleCardClick(attack, 'attack')} onNewScore={(atk) => atk.status === 'completed' && setFormModal({ type: 'score', initialValues: { attack_id: atk.id } })} />
                    ))
                  }
                </PipelineColumn>

                <PipelineColumn
                  tourId="scores"
                  addLabel="New Score"
                  onAdd={() => setFormModal({ type: 'score' })}
                  description="Evaluate attack responses against 22 child safety principles. Each response gets a 0-5 score across categories like safety, age-appropriateness, and ethics."
                  loading={loading.scores}
                  error={error.scores}
                >
                  {filteredScores.length === 0 ? <EmptyState message="No scores yet" /> :
                    filteredScores.map(score => (
                      <ScoreCard key={score.id} score={score} selected={selectedScore?.id === score.id} onClick={() => handleCardClick(score, 'score')} onReport={openReport} onNewGuardrail={(sc) => sc.status === 'completed' && setFormModal({ type: 'guardrail', initialValues: { score_id: sc.id } })} />
                    ))
                  }
                </PipelineColumn>

                <PipelineColumn
                  tourId="guardrails"
                  addLabel="Generate Rules"
                  onAdd={() => setFormModal({ type: 'guardrail' })}
                  description="Auto-generate guardrail rules based on scoring failures. These rules can be added to your AI system prompt to prevent future issues."
                  loading={loading.guardrails}
                  error={error.guardrails}
                >
                  {filteredGuardrails.length === 0 ? <EmptyState message="No guardrails yet" /> :
                    filteredGuardrails.map(guardrail => (
                      <GuardrailCard key={guardrail.id} guardrail={guardrail} selected={selectedGuardrail?.id === guardrail.id} onClick={() => handleCardClick(guardrail, 'guardrail')} />
                    ))
                  }
                </PipelineColumn>
              </div>
            </div>
          </div>

          {/* Logs Panel - Always visible at bottom */}
          <LogsPanel />
        </div>

        {/* Right Sidebar */}
        {showPanel && (
          <div
            className="fixed top-[57px] right-0 bottom-0 bg-white border-l border-gray-200 flex flex-col transition-all duration-300"
            style={{ width: panelWidth }}
          >
            {/* Collapse/Expand Toggle */}
            <button
              onClick={() => setPanelCollapsed(!panelCollapsed)}
              className="absolute -left-6 top-1/2 -translate-y-1/2 w-6 h-16 bg-white border border-r-0 border-gray-200 flex items-center justify-center hover:bg-gray-50 transition-colors"
            >
              <svg className={`w-4 h-4 text-gray-400 transition-transform ${panelCollapsed ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            {panelCollapsed ? (
              /* Collapsed state - vertical label */
              <div className="flex-1 flex items-center justify-center">
                <div className="text-gray-400 text-xs uppercase tracking-wider font-medium" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
                  {detailPanel.type} Details
                </div>
              </div>
            ) : (
              /* Expanded state - full content */
              <DetailPanel
                item={detailPanel.item}
                type={detailPanel.type}
                onClose={() => setDetailPanel({ item: null, type: null })}
                onReport={openReport}
                onViewRecords={openAttackRecords}
                onViewGuardrails={openGuardrails}
                onDelete={refreshAll}
                endpoints={endpoints}
                attacks={attacks}
                scores={scores}
              />
            )}
          </div>
        )}
      </div>

      {/* Report Modal */}
      {reportModal && (
        <ReportModal
          score={reportModal}
          attacks={attacks}
          endpoints={endpoints}
          onClose={() => setReportModal(null)}
        />
      )}

      {/* Attack Records Modal */}
      {attackRecordsModal && (
        <AttackRecordsModal
          attack={attackRecordsModal}
          onClose={() => setAttackRecordsModal(null)}
        />
      )}

      {/* Guardrails Modal */}
      {guardrailsModal && (
        <GuardrailsModal
          guardrail={guardrailsModal}
          onClose={() => setGuardrailsModal(null)}
        />
      )}

      {/* Form Modal */}
      {formModal && (
        <FormModal
          key={`${formModal.type}-${JSON.stringify(formModal.initialValues || {})}`}
          title={formConfigs[formModal.type].title}
          fields={formConfigs[formModal.type].fields}
          onSubmit={handleFormSubmit}
          onClose={() => setFormModal(null)}
          loading={formLoading}
          initialValues={formModal.initialValues || {}}
        />
      )}
    </div>
  );
};

export default Dashboard;
