import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, Trash2, FolderGit, AlertCircle, Calendar } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export const DashboardPage: React.FC = () => {
  const { token, user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/projects/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        throw new Error('Failed to retrieve project list.');
      }
      const data = await response.json();
      setProjects(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend api');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProjects();
    }
  }, [token]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!name.trim()) {
      setFormError("Project Name is required.");
      return;
    }
    
    setCreating(true);
    try {
      const response = await fetch('/api/v1/projects/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name, description }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Could not initialize project');
      }

      setName('');
      setDescription('');
      await fetchProjects();
    } catch (err: any) {
      setFormError(err.message || 'Creation failed');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm("Are you sure you want to permanently delete this project?")) {
      return;
    }
    try {
      const response = await fetch(`/api/v1/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Deletion failed');
      }

      await fetchProjects();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Title section */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-extrabold text-textPrimary tracking-tight">Projects Hub</h2>
          <p className="text-textSecondary text-sm mt-1">Manage, index, and analyze your enterprise codebases.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Project Creation Form Panel */}
        <div className="lg:col-span-1 p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4">
          <h3 className="text-lg font-bold text-textPrimary flex items-center gap-2">
            <Plus size={18} className="text-primary" />
            Initialize Project
          </h3>
          
          {formError && (
            <div className="p-3 rounded bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
              <AlertCircle size={14} className="shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleCreateProject} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-textSecondary uppercase tracking-wider mb-1.5">
                Project Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CodeAtlas Core"
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-textPrimary focus:outline-none focus:border-primary transition"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-textSecondary uppercase tracking-wider mb-1.5">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe this repository or snapshot scope..."
                rows={3}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-textPrimary focus:outline-none focus:border-primary transition"
              />
            </div>
            <button
              type="submit"
              disabled={creating}
              className="w-full py-2.5 px-4 bg-primary hover:bg-primaryHover text-white text-sm font-semibold rounded-lg shadow-lg shadow-primary/10 transition-all duration-200 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {creating ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  <Plus size={16} />
                  Create Project
                </>
              )}
            </button>
          </form>
        </div>

        {/* Projects List Grid */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-bold text-textPrimary">Active Projects</h3>
          
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 border border-border/60 bg-surface/20 rounded-xl">
              <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin"></div>
              <p className="mt-3 text-textSecondary text-xs">Loading projects...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-400 text-sm">
              {error}
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center p-12 border border-dashed border-border rounded-xl bg-surface/20 space-y-2">
              <FolderGit size={32} className="mx-auto text-textSecondary" />
              <p className="text-sm text-textSecondary font-medium">No projects configured yet</p>
              <p className="text-xs text-textSecondary/70">Create a project using the sidebar panel to begin repository analysis.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {projects.map((project) => (
                <div key={project.id} className="p-5 rounded-xl bg-surface border border-border/80 shadow-md hover:border-primary/50 hover:shadow-lg transition-all duration-200 flex flex-col justify-between h-44">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-textPrimary text-base truncate pr-2">{project.name}</h4>
                      <FolderGit className="text-primary/70 shrink-0" size={18} />
                    </div>
                    <p className="text-xs text-textSecondary line-clamp-3 leading-relaxed">
                      {project.description || "No description provided."}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-border/40 mt-3">
                    <span className="text-[10px] text-textSecondary/80 flex items-center gap-1">
                      <Calendar size={12} />
                      {formatDate(project.created_at)}
                    </span>
                    {user?.role === 'ADMIN' && (
                      <button
                        onClick={() => handleDeleteProject(project.id)}
                        className="text-red-400 hover:text-red-300 p-1.5 rounded hover:bg-red-500/10 transition"
                        title="Delete project workspace"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
