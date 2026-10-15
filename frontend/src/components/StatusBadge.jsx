import React from 'react';

export const StatusBadge = ({ status }) => {
  if (!status) return null;

  const s = String(status).toUpperCase();

  let style = 'badge-secondary';

  if (['ELIGIBLE', 'ONLINE', 'VALID', 'SERVICE_COMPLETED', 'RESOLVED', 'AVAILABLE'].includes(s)) {
    style = 'badge-success';
  } else if (['DUE_SOON', 'WARNING', 'HOLD', 'QUEUED', 'ACKNOWLEDGED', 'RESERVED'].includes(s)) {
    style = 'badge-warning';
  } else if (['NOT_ELIGIBLE', 'OFFLINE', 'INVALID', 'EXPIRED', 'VERIFICATION_FAILED', 'OPEN', 'CRITICAL', 'HIGH', 'BLOCKED', 'MAINTENANCE'].includes(s)) {
    style = 'badge-danger';
  } else if (['BAY_ASSIGNED', 'IN_SERVICE', 'ENTERED', 'IDENTIFIED', 'VERIFIED'].includes(s)) {
    style = 'badge-info';
  } else if (['EXITED'].includes(s)) {
    style = 'badge-purple';
  }

  return (
    <span className={`badge ${style}`}>
      {s.replace(/_/g, ' ')}
    </span>
  );
};
