import React from 'react';

export const Timeline = ({ events }) => {
  if (!events || events.length === 0) {
    return <div className="text-sm text-slate-500 py-4">No chronological events recorded yet.</div>;
  }

  return (
    <div className="timeline">
      {events.map((evt, idx) => (
        <div key={evt.id || idx} className="timeline-item">
          <div className="timeline-marker" />
          <div className="timeline-content">
            <div className="flex-between">
              <span className="font-semibold text-sm text-slate-200 uppercase">
                {evt.new_state ? evt.new_state.replace(/_/g, ' ') : evt.event_source}
              </span>
              <span className="timeline-time font-mono">
                {new Date(evt.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {evt.previous_state && (
              <p className="text-xs text-slate-400 mt-1">
                Transitioned from <span className="font-medium text-slate-300">{evt.previous_state}</span> → <span className="font-medium text-blue-400">{evt.new_state}</span>
              </p>
            )}

            {evt.reason && (
              <p className="text-xs text-amber-300/90 mt-1 italic">
                Reason: {evt.reason}
              </p>
            )}

            <div className="flex-between mt-2 pt-2 border-t border-slate-800 text-[11px] text-slate-500 font-mono">
              <span>Source: {evt.event_source}</span>
              {evt.operator_id && <span>Operator ID: #{evt.operator_id}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
