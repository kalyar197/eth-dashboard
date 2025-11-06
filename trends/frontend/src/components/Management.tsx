// src/components/Management.tsx
/**
 * Management Tab - Keyword CRUD operations
 * Minimalist table with add/delete functionality
 */

import { useState, useEffect } from 'react';
import { getKeywords, addKeyword, deleteKeyword, type Keyword } from '../lib/api';

export function Management() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [newKeyword, setNewKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load keywords on mount
  useEffect(() => {
    fetchKeywords();
  }, []);

  const fetchKeywords = async () => {
    try {
      const data = await getKeywords();
      setKeywords(data);
      setError(null);
    } catch (err) {
      setError('Failed to load keywords');
      console.error(err);
    }
  };

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await addKeyword(newKeyword.trim());
      setNewKeyword('');
      fetchKeywords(); // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add keyword');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteKeyword = async (id: string, keyword: string) => {
    if (!confirm(`Delete "${keyword}"?`)) return;

    try {
      await deleteKeyword(id);
      fetchKeywords(); // Refresh list
    } catch (err) {
      setError('Failed to delete keyword');
      console.error(err);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge badge-success">✓ Done</span>;
      case 'in_progress':
        return <span className="badge badge-warning">⟳ Fetching</span>;
      case 'partial':
        return <span className="badge badge-warning">⚠ Partial</span>;
      case 'failed':
        return <span className="badge badge-error">✗ Failed</span>;
      default:
        return <span className="badge">Pending</span>;
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Add Keyword Form */}
      <div className="flex gap-2">
        <input
          type="text"
          className="input flex-1"
          placeholder="Enter keyword (e.g., bitcoin, ethereum)"
          value={newKeyword}
          onChange={(e) => setNewKeyword(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
          disabled={loading}
        />
        <button
          className="btn"
          onClick={handleAddKeyword}
          disabled={loading || !newKeyword.trim()}
        >
          {loading ? 'Adding...' : 'Add'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-900/20 border border-red-900 rounded text-red-100 text-sm">
          {error}
        </div>
      )}

      {/* Keywords Table */}
      <table className="table">
        <thead>
          <tr>
            <th>Keyword</th>
            <th>Created</th>
            <th>Last Updated</th>
            <th>Status</th>
            <th>Regions</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {keywords.length === 0 ? (
            <tr>
              <td colSpan={6} className="text-center text-muted py-8">
                No keywords yet. Add one above to get started.
              </td>
            </tr>
          ) : (
            keywords.map((kw) => (
              <tr key={kw.id}>
                <td className="font-bold">{kw.keyword}</td>
                <td>{new Date(kw.created_at).toLocaleDateString()}</td>
                <td>{new Date(kw.last_updated).toLocaleDateString()}</td>
                <td>{getStatusBadge(kw.status)}</td>
                <td className="text-muted text-xs">
                  {kw.completed_regions?.length || 0} / {kw.regions?.length || 0}
                </td>
                <td>
                  <button
                    className="btn-secondary text-xs px-2 py-1"
                    onClick={() => handleDeleteKeyword(kw.id, kw.keyword)}
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {/* Info */}
      <div className="text-xs text-muted mt-4">
        {keywords.length} keyword{keywords.length !== 1 ? 's' : ''} tracked
      </div>
    </div>
  );
}
