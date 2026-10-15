import React from 'react';
import { Users, Shield } from 'lucide-react';

export const UserManagementPage = () => {
  const users = [
    { id: 1, email: 'operator@sitea.com', name: 'Alex Operator', role: 'Operator', site: 'North Terminal' },
    { id: 2, email: 'sitemanager@sitea.com', name: 'Sarah Site Manager', role: 'Site Manager', site: 'North Terminal' },
    { id: 3, email: 'regional@system.com', name: 'Robert Regional Director', role: 'Regional Manager', site: 'All Sites' },
    { id: 4, email: 'auditor@system.com', name: 'Amanda Auditor', role: 'Auditor', site: 'All Sites' },
    { id: 5, email: 'admin@system.com', name: 'Arthur System Admin', role: 'Admin', site: 'All Sites' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-400" />
            <span>RBAC User & Role Management</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Role-Based Access Control Credentials & Station Scope</p>
        </div>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Assigned Station Scope</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="font-semibold text-slate-200">{u.name}</td>
                  <td className="font-mono text-xs text-slate-400">{u.email}</td>
                  <td>
                    <span className="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {u.role}
                    </span>
                  </td>
                  <td className="text-xs text-slate-300 font-mono">{u.site}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
