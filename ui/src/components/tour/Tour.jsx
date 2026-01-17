import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTour } from './TourContext';

// Tour step definitions
const TOUR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to Emotional Reliance Testing',
    content: `This tool helps you evaluate AI systems for behaviors that may foster emotional reliance in children and young people.

We test against 15 behaviors across 3 cues:
• Anthropomorphic - AI claiming emotions, sensations, or personhood
• Interactional - Flattery, mimicry, excessive validation
• Relational - Exclusivity claims, relationship labels, intrusiveness

Let's walk through the workflow!`,
    target: null, // Full-screen welcome
    placement: 'center',
    route: '/',
  },
  {
    id: 'endpoints',
    title: '1. Add Your Endpoints',
    content: `Start by adding AI endpoints you want to test. These can be:
• OpenAI-compatible APIs (GPT, Claude, etc.)
• Simple HTTP endpoints (your custom chatbot)

Click "Add Endpoint" to connect your first AI system.`,
    target: '[data-tour="endpoints"]',
    placement: 'right',
    route: '/',
  },
  {
    id: 'attacks',
    title: '2. Run Attacks',
    content: `"Attacks" are test runs that send adversarial prompts to your endpoint.

Prompts are designed to probe for emotional reliance behaviors - like asking the AI to be a "best friend" or express personal feelings.

Select an endpoint and dataset, then run the attack.`,
    target: '[data-tour="attacks"]',
    placement: 'right',
    route: '/',
  },
  {
    id: 'scores',
    title: '3. Score Responses',
    content: `After an attack completes, score the responses.

Multiple AI judges evaluate each response against our 15 criteria. You can configure:
• Age context (child, teen, young adult)
• Evaluation judge (different weighting profiles)

Scores range from 1 (safe) to 5 (concerning).`,
    target: '[data-tour="scores"]',
    placement: 'left',
    route: '/',
  },
  {
    id: 'guardrails',
    title: '4. Generate Guardrails',
    content: `For responses that scored poorly, generate guardrail rules.

These are system prompt additions you can use to prevent similar issues in the future.

Rules are specific and actionable - copy them directly into your AI's configuration.`,
    target: '[data-tour="guardrails"]',
    placement: 'left',
    route: '/',
  },
  {
    id: 'datasets',
    title: 'Datasets: View, Edit & Test',
    content: `Manage your prompt datasets here:
• View built-in datasets covering all 15 behaviors
• Create and edit custom datasets
• Test prompts against endpoints in real-time
• See coverage across all behaviors

Switch between Prompts and Coverage views to explore.`,
    target: '[data-tour="datasets-nav"]',
    placement: 'bottom',
    route: '/',
  },
  {
    id: 'judges',
    title: 'Judges: Configure Evaluation',
    content: `Judges are context-specific evaluation profiles.

Different use cases need different evaluation weights:
• Educational AI - stricter on relationship boundaries
• Companionship AI - stricter on emotional claims
• Entertainment AI - more lenient overall

Create custom judges with your own weight adjustments.`,
    target: '[data-tour="judges-nav"]',
    placement: 'bottom',
    route: '/',
  },
  {
    id: 'config',
    title: 'Model Configuration',
    content: `Click these buttons to configure:
• Judges - Which LLM models evaluate responses
• Generators - Which LLM generates guardrail rules

You can test configurations before applying them.`,
    target: '[data-tour="config-buttons"]',
    placement: 'bottom',
    route: '/',
  },
  {
    id: 'complete',
    title: 'Ready to Start!',
    content: `That's the full workflow:

1. Add Endpoint → 2. Run Attack → 3. Score → 4. Generate Guardrails

You can restart this tour anytime by clicking the "?" button in the top bar.

Good luck making AI safer for young people!`,
    target: null,
    placement: 'center',
    route: '/',
  },
];

export const Tour = () => {
  const { isActive, currentStep, endTour, nextStep, prevStep } = useTour();
  const navigate = useNavigate();
  const location = useLocation();
  const [targetRect, setTargetRect] = useState(null);

  const step = TOUR_STEPS[currentStep];
  const isLastStep = currentStep === TOUR_STEPS.length - 1;
  const isFirstStep = currentStep === 0;

  // Navigate to correct route for step
  useEffect(() => {
    if (isActive && step?.route && location.pathname !== step.route) {
      navigate(step.route);
    }
  }, [isActive, step, location.pathname, navigate]);

  // Find and track target element
  useEffect(() => {
    if (!isActive || !step?.target) {
      setTargetRect(null);
      return;
    }

    const updateRect = () => {
      const el = document.querySelector(step.target);
      if (el) {
        const rect = el.getBoundingClientRect();
        setTargetRect(rect);
      } else {
        setTargetRect(null);
      }
    };

    // Initial update with delay for DOM to settle
    const timeout = setTimeout(updateRect, 100);

    // Update on resize/scroll
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);

    return () => {
      clearTimeout(timeout);
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [isActive, step, currentStep]);

  // Keyboard navigation
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        endTour(false);
      } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
        if (isLastStep) {
          endTour(true);
        } else {
          nextStep();
        }
      } else if (e.key === 'ArrowLeft') {
        if (!isFirstStep) {
          prevStep();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isActive, isLastStep, isFirstStep, endTour, nextStep, prevStep]);

  if (!isActive || !step) return null;

  const isCentered = !step.target || !targetRect;

  // Calculate tooltip position
  const getTooltipStyle = () => {
    if (isCentered) {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 16;
    const tooltipWidth = 360;
    const tooltipHeight = 280;

    let top, left;

    switch (step.placement) {
      case 'right':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.right + padding;
        break;
      case 'left':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.left - tooltipWidth - padding;
        break;
      case 'bottom':
        top = targetRect.bottom + padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      case 'top':
        top = targetRect.top - tooltipHeight - padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      default:
        top = targetRect.bottom + padding;
        left = targetRect.left;
    }

    // Keep tooltip in viewport
    top = Math.max(padding, Math.min(window.innerHeight - tooltipHeight - padding, top));
    left = Math.max(padding, Math.min(window.innerWidth - tooltipWidth - padding, left));

    return {
      position: 'fixed',
      top,
      left,
      width: tooltipWidth,
    };
  };

  return (
    <div className="fixed inset-0 z-[9999]">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60 transition-opacity duration-300" />

      {/* Spotlight cutout */}
      {targetRect && (
        <div
          className="absolute bg-transparent rounded-xl ring-4 ring-everyone-blue ring-offset-4 ring-offset-transparent transition-all duration-300"
          style={{
            top: targetRect.top - 8,
            left: targetRect.left - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
            boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.6)',
          }}
        />
      )}

      {/* Tooltip */}
      <div
        className="bg-white rounded-2xl shadow-2xl p-6 max-w-[360px] animate-fade-in"
        style={getTooltipStyle()}
      >
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-3">
          <div className="flex gap-1">
            {TOUR_STEPS.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-colors ${
                  i === currentStep ? 'bg-everyone-blue' : i < currentStep ? 'bg-everyone-blue/40' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <span className="text-xs text-gray-400 ml-auto">
            {currentStep + 1} / {TOUR_STEPS.length}
          </span>
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-gray-800 mb-3 font-display">{step.title}</h3>
        <p className="text-sm text-gray-600 whitespace-pre-line leading-relaxed mb-6">{step.content}</p>

        {/* Navigation */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => endTour(true)}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Skip tour
          </button>
          <div className="flex-1" />
          {!isFirstStep && (
            <button
              onClick={prevStep}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
            >
              Back
            </button>
          )}
          <button
            onClick={() => isLastStep ? endTour(true) : nextStep()}
            className="px-5 py-2 bg-everyone-blue hover:bg-everyone-blue/90 text-white text-sm font-medium rounded-xl transition-colors"
          >
            {isLastStep ? 'Get Started' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Tour;
