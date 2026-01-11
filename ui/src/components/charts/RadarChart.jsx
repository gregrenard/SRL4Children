const getScoreColor = (score) => {
  if (score < 2.5) return '#e53e3e';
  if (score < 3.5) return '#d69e2e';
  return '#38a169';
};

// Simple bar display for 1-2 categories
const CategoryBars = ({ categoryScores }) => {
  const categories = Object.entries(categoryScores);

  return (
    <div className="w-full max-w-sm mx-auto space-y-4 py-4">
      {categories.map(([cat, score]) => (
        <div key={cat} className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700 capitalize">{cat}</span>
            <span
              className="text-lg font-bold"
              style={{ color: getScoreColor(score) }}
            >
              {score.toFixed(1)}/5.0
            </span>
          </div>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${(score / 5) * 100}%`,
                backgroundColor: getScoreColor(score)
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400">
            <span>Poor</span>
            <span>Fair</span>
            <span>Good</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export const RadarChart = ({ categoryScores }) => {
  if (!categoryScores || Object.keys(categoryScores).length === 0) {
    return <div className="text-center text-gray-400 py-8">No category scores available</div>;
  }

  const categories = Object.keys(categoryScores);

  // For 1-2 categories, show bar chart instead of radar
  if (categories.length < 3) {
    return <CategoryBars categoryScores={categoryScores} />;
  }

  const size = 280;
  const center = size / 2;
  const maxRadius = 100;
  const angleStep = (2 * Math.PI) / categories.length;

  const getPoint = (value, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const radius = (value / 5) * maxRadius;
    return { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) };
  };

  const getLabelPoint = (index) => {
    const angle = index * angleStep - Math.PI / 2;
    const radius = maxRadius + 35;
    return { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) };
  };

  const getZonePath = (outerRadius) => {
    const points = categories.map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return { x: center + outerRadius * Math.cos(angle), y: center + outerRadius * Math.sin(angle) };
    });
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
  };

  const dataPoints = categories.map((cat, i) => getPoint(categoryScores[cat] || 0, i));
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  const gridLines = [1, 2, 3, 4, 5].map(level => {
    const radius = (level / 5) * maxRadius;
    const points = categories.map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      return { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) };
    });
    return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';
  });

  return (
    <svg width={size} height={size} className="mx-auto">
      <path d={getZonePath(maxRadius)} className="radar-zone-green" />
      <path d={getZonePath((3.5/5) * maxRadius)} className="radar-zone-yellow" />
      <path d={getZonePath((2.5/5) * maxRadius)} className="radar-zone-red" />

      {gridLines.map((path, i) => (
        <path key={i} d={path} fill="none" stroke="rgba(0,0,0,0.1)" strokeWidth="1" />
      ))}

      {categories.map((_, i) => {
        const end = getPoint(5, i);
        return <line key={i} x1={center} y1={center} x2={end.x} y2={end.y} stroke="rgba(0,0,0,0.1)" strokeWidth="1" />;
      })}

      <path d={dataPath} fill="rgba(119,143,191,0.3)" stroke="#778fbf" strokeWidth="2" />

      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r="4" fill="#778fbf" stroke="white" strokeWidth="2" />
      ))}

      {categories.map((cat, i) => {
        const labelPos = getLabelPoint(i);
        const score = categoryScores[cat] || 0;
        return (
          <g key={i}>
            <text x={labelPos.x} y={labelPos.y - 6} textAnchor="middle" className="fill-gray-600 text-xs font-medium capitalize">
              {cat}
            </text>
            <text
              x={labelPos.x} y={labelPos.y + 10} textAnchor="middle"
              className="text-sm font-semibold"
              style={{ fill: getScoreColor(score) }}
            >
              {score.toFixed(1)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};
