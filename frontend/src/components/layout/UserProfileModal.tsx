import React, { useState, useEffect } from 'react';
import { api, UserProfileResponse } from '../../services/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const UserProfileModal: React.FC<Props> = ({ isOpen, onClose }) => {
  // Current user state
  const [profile, setProfile] = useState<UserProfileResponse>({
    username: 'operator',
    role: 'OPERATOR',
    name: 'Insp. S. Sharma',
    agency: 'Kamrup Metro Logistics Desk',
    email: 'insp.sharma@asdma.gov.in',
    phone: '+91 94350 22002',
    avatar_url: '/officer_sharma.png',
  });

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    agency: '',
  });

  // Password change state
  const [isPasswordSectionOpen, setIsPasswordSectionOpen] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Preference toggles
  const [showBadges, setShowBadges] = useState(true);
  const [auditoryAlerts, setAuditoryAlerts] = useState(true);

  // Load user profile from backend
  const fetchProfile = async () => {
    setIsLoading(true);
    setStatusMessage(null);
    try {
      const data = await api.getAuthMe();
      if (data) {
        setProfile(data);
        setFormData({
          name: data.name || '',
          email: data.email || '',
          phone: data.phone || '',
          agency: data.agency || '',
        });
      }
    } catch (err: any) {
      console.warn('Could not fetch latest profile from backend:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchProfile();
      setIsEditing(false);
      setIsPasswordSectionOpen(false);
      setStatusMessage(null);
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Handle Edit Mode Toggle
  const handleStartEdit = () => {
    setFormData({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      agency: profile.agency || '',
    });
    setStatusMessage(null);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setFormData({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      agency: profile.agency || '',
    });
    setStatusMessage(null);
    setIsEditing(false);
  };

  // Validate and Save Profile
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMessage(null);

    // Validation
    const trimmedName = formData.name.trim();
    if (trimmedName.length < 2) {
      setStatusMessage({ type: 'error', text: 'Full Name must be at least 2 characters long.' });
      return;
    }

    const trimmedEmail = formData.email.trim();
    if (trimmedEmail && (!trimmedEmail.includes('@') || !trimmedEmail.split('@')[1]?.includes('.'))) {
      setStatusMessage({ type: 'error', text: 'Please enter a valid official email address.' });
      return;
    }

    setIsSaving(true);
    try {
      const updated = await api.updateProfile({
        name: trimmedName,
        email: trimmedEmail,
        phone: formData.phone.trim(),
        agency: formData.agency.trim(),
      });

      setProfile(updated);
      setIsEditing(false);
      setStatusMessage({
        type: 'success',
        text: 'Officer dossier successfully updated and persisted in ASDMA registry.',
      });

      // Notify other components (Topbar, Sidebar)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('reliefos-profile-updated', { detail: updated }));
      }
    } catch (err: any) {
      const errDetail = err?.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : err?.message || 'Failed to update profile.';
      setStatusMessage({ type: 'error', text: errMsg });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle Password Change
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMessage(null);

    if (!passwordForm.currentPassword) {
      setStatusMessage({ type: 'error', text: 'Please enter your current operational password.' });
      return;
    }

    if (passwordForm.newPassword.length < 6) {
      setStatusMessage({ type: 'error', text: 'New password must be at least 6 characters long.' });
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setStatusMessage({ type: 'error', text: 'New password and confirmation do not match.' });
      return;
    }

    if (passwordForm.newPassword === passwordForm.currentPassword) {
      setStatusMessage({ type: 'error', text: 'New password cannot be the same as your current password.' });
      return;
    }

    setIsChangingPassword(true);
    try {
      const res = await api.changePassword({
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword,
      });

      if (res.success) {
        setStatusMessage({ type: 'success', text: 'Operational access password updated successfully.' });
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
        setIsPasswordSectionOpen(false);
      }
    } catch (err: any) {
      const errDetail = err?.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : err?.message || 'Password update failed.';
      setStatusMessage({ type: 'error', text: errMsg });
    } finally {
      setIsChangingPassword(false);
    }
  };

  // Handle Logout
  const handleLogout = () => {
    api.logout();
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  // Officer initials fallback
  const getInitials = (nameStr: string) => {
    const parts = nameStr.replace(/^(Insp\.|Dr\.|Mr\.|Ms\.|EOC)\s*/i, '').trim().split(/\s+/);
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return (parts[0]?.[0] || 'OP').toUpperCase();
  };

  // RBAC Permission checks based on real role
  const roleUpper = (profile.role || 'OPERATOR').toUpperCase();
  const isCommander = roleUpper === 'COMMANDER';
  const isOperatorOrCommander = roleUpper === 'COMMANDER' || roleUpper === 'OPERATOR';

  return (
    <div className="fixed inset-0 z-[1200] flex items-start justify-end p-4 pt-16 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0e1d2c] border border-outline-variant/50 rounded-xl shadow-2xl w-full max-w-xl max-h-[88vh] overflow-y-auto p-space-lg text-on-surface flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-space-sm mb-space-md">
          <div className="flex items-center gap-space-sm">
            <span className="material-symbols-outlined text-primary text-[24px]">badge</span>
            <div>
              <h2 className="font-headline-sm text-headline-sm font-bold tracking-tight">
                Operator Profile & Duty Dossier
              </h2>
              <span className="font-mono-data text-[10px] text-outline">
                ASDMA Incident Command Protocol • Assam State Disaster Management Authority
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
            title="Close Dossier"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Status / Alert Banner */}
        {statusMessage && (
          <div
            className={`p-3 rounded-lg mb-space-md flex items-center gap-2.5 text-[12px] font-mono-data border animate-fadeIn ${
              statusMessage.type === 'success'
                ? 'bg-primary/10 border-primary/40 text-primary'
                : 'bg-error/10 border-error/40 text-error'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">
              {statusMessage.type === 'success' ? 'check_circle' : 'error'}
            </span>
            <span className="flex-1 font-medium">{statusMessage.text}</span>
            <button
              onClick={() => setStatusMessage(null)}
              className="hover:opacity-75 text-on-surface-variant p-0.5"
            >
              <span className="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>
        )}

        {/* Loading Spinner for initial fetch */}
        {isLoading ? (
          <div className="p-8 flex flex-col items-center justify-center gap-2 text-outline">
            <span className="material-symbols-outlined animate-spin text-[28px] text-primary">sync</span>
            <span className="font-mono-data text-[12px]">Synchronizing officer records with backend...</span>
          </div>
        ) : (
          <>
            {/* Officer Header Card */}
            <div className="bg-surface-container p-space-md rounded-lg border border-outline-variant/30 flex items-center gap-space-md mb-space-md relative overflow-hidden">
              {/* Profile Avatar / Initials */}
              <div className="w-16 h-16 rounded-lg overflow-hidden border border-primary/40 flex-shrink-0 bg-surface-container-high flex items-center justify-center relative">
                {profile.avatar_url ? (
                  <img
                    src={profile.avatar_url}
                    alt={profile.name}
                    className="w-full h-full object-cover object-top"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                ) : null}
                <span className="font-mono-data font-bold text-[18px] text-primary absolute pointer-events-none -z-0">
                  {getInitials(profile.name)}
                </span>
              </div>

              {/* Officer Details & Badges */}
              <div className="flex flex-col min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-headline-sm text-[16px] font-bold text-on-surface truncate">
                    {profile.name}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1 ${
                      isCommander
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-primary-container/20 text-primary border-primary/30'
                    }`}
                  >
                    <span className="material-symbols-outlined text-[12px]">verified_user</span>
                    {profile.role}
                  </span>
                </div>
                <span className="font-mono-data text-[11px] text-secondary mt-0.5">
                  ID: ASDMA-EMP-8841-{profile.username.toUpperCase()} • Duty: {profile.agency || 'Guwahati EOC Hub'}
                </span>
                <span className="font-body-sm text-[11px] text-on-surface-variant truncate">
                  Official Contact: {profile.email || 'officer@asdma.gov.in'} • {profile.phone || '+91 94350 00000'}
                </span>
              </div>

              {/* Edit Mode Toggle Button */}
              {!isEditing && (
                <button
                  type="button"
                  onClick={handleStartEdit}
                  className="px-3 py-1.5 rounded bg-surface-container-high hover:bg-surface-container-highest text-primary border border-primary/30 text-[12px] font-medium flex items-center gap-1.5 transition-colors self-start shadow-xs"
                  title="Edit Officer Profile"
                >
                  <span className="material-symbols-outlined text-[16px]">edit</span>
                  Edit
                </button>
              )}
            </div>

            {/* Profile Fields Section: View Mode vs Edit Mode */}
            {isEditing ? (
              <form onSubmit={handleSaveProfile} className="bg-surface-container-lowest p-space-md rounded-lg border border-primary/30 mb-space-md space-y-3">
                <div className="flex items-center justify-between pb-1 border-b border-outline-variant/20">
                  <span className="font-label-sm text-[11px] uppercase tracking-wider text-primary font-bold flex items-center gap-1">
                    <span className="material-symbols-outlined text-[15px]">edit_note</span>
                    Edit Profile Details
                  </span>
                  <span className="font-mono-data text-[10px] text-outline">All changes persist to database</span>
                </div>

                {/* Full Name Field */}
                <div>
                  <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                    Full Officer Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    minLength={2}
                    placeholder="e.g. Insp. S. Sharma"
                    className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                {/* Email Field */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                      Official Email *
                    </label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      placeholder="e.g. insp.sharma@asdma.gov.in"
                      className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                    />
                  </div>

                  {/* Phone Field */}
                  <div>
                    <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="e.g. +91 94350 22002"
                      className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                    />
                  </div>
                </div>

                {/* Agency / Station Field */}
                <div>
                  <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                    Duty Station / Logistics Desk
                  </label>
                  <input
                    type="text"
                    value={formData.agency}
                    onChange={(e) => setFormData({ ...formData, agency: e.target.value })}
                    placeholder="e.g. Kamrup Metro Logistics Desk"
                    className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                {/* RBAC Role - Strictly Read-Only with Security Notice */}
                <div className="p-2.5 rounded bg-surface-container/60 border border-outline-variant/30 flex items-start gap-2">
                  <span className="material-symbols-outlined text-[18px] text-amber-400 mt-0.5">lock</span>
                  <div className="flex flex-col text-[11px]">
                    <span className="font-semibold text-on-surface flex items-center gap-1.5">
                      Role Tier: <span className="font-mono-data text-primary uppercase font-bold">{profile.role}</span> (Read-Only)
                    </span>
                    <span className="text-on-surface-variant text-[10.5px] mt-0.5">
                      Role privileges and authorization levels are strictly managed by District EOC Administration. Users cannot alter system RBAC tiers from the profile interface.
                    </span>
                  </div>
                </div>

                {/* Edit Form Action Buttons */}
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/20">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    disabled={isSaving}
                    className="px-3 py-1.5 rounded bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-[12px] font-medium transition-colors border border-outline-variant/40"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-1.5 rounded bg-primary text-on-primary font-semibold text-[12px] hover:brightness-110 transition-all flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
                  >
                    {isSaving ? (
                      <>
                        <span className="material-symbols-outlined animate-spin text-[16px]">sync</span>
                        Saving Changes...
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined text-[16px]">check</span>
                        Save Changes
                      </>
                    )}
                  </button>
                </div>
              </form>
            ) : (
              /* View Mode Information Grid */
              <div className="bg-surface-container-lowest p-space-md rounded-lg border border-outline-variant/30 mb-space-md">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-outline-variant/20">
                  <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold">
                    Operational Identification Dossier
                  </span>
                  <span className="font-mono-data text-[10.5px] text-primary flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                    Verified ASDMA Record
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-[12px]">
                  <div>
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Official Name</span>
                    <span className="font-semibold text-on-surface">{profile.name}</span>
                  </div>
                  <div>
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Username</span>
                    <span className="font-mono-data text-secondary">@{profile.username}</span>
                  </div>
                  <div>
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Official Email</span>
                    <span className="text-on-surface truncate block" title={profile.email}>{profile.email || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Contact Phone</span>
                    <span className="font-mono-data text-on-surface">{profile.phone || 'N/A'}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Assigned Logistics Desk</span>
                    <span className="text-on-surface">{profile.agency || 'Kamrup Metro District Control Room'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Password & Security Management Accordion */}
            <div className="bg-surface-container-lowest rounded-lg border border-outline-variant/30 mb-space-md overflow-hidden">
              <button
                type="button"
                onClick={() => {
                  setIsPasswordSectionOpen(!isPasswordSectionOpen);
                  setStatusMessage(null);
                }}
                className="w-full p-3 flex items-center justify-between bg-surface-container/40 hover:bg-surface-container/70 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-[18px]">password</span>
                  <span className="text-[12px] font-semibold text-on-surface">
                    Security Credentials & Password Management
                  </span>
                </div>
                <span className="material-symbols-outlined text-[18px] text-outline transition-transform duration-200">
                  {isPasswordSectionOpen ? 'expand_less' : 'expand_more'}
                </span>
              </button>

              {isPasswordSectionOpen && (
                <form onSubmit={handleChangePassword} className="p-space-md border-t border-outline-variant/20 space-y-3 bg-surface-container-low/50">
                  <p className="text-[11px] text-on-surface-variant font-body-sm leading-tight">
                    Change your operational command password. Password requires verification of your current password and a minimum of 6 characters.
                  </p>

                  <div>
                    <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                      Current Password *
                    </label>
                    <input
                      type="password"
                      value={passwordForm.currentPassword}
                      onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                      required
                      placeholder="Enter current password"
                      className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                        New Password *
                      </label>
                      <input
                        type="password"
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                        required
                        minLength={6}
                        placeholder="Min 6 characters"
                        className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                        Confirm New Password *
                      </label>
                      <input
                        type="password"
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                        required
                        minLength={6}
                        placeholder="Confirm new password"
                        className="w-full px-3 py-1.5 rounded bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/20">
                    <button
                      type="button"
                      onClick={() => {
                        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
                        setIsPasswordSectionOpen(false);
                      }}
                      className="px-3 py-1.5 rounded bg-surface-container text-on-surface-variant text-[12px] hover:text-on-surface transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isChangingPassword}
                      className="px-4 py-1.5 rounded bg-secondary-container text-on-secondary-container font-semibold text-[12px] hover:brightness-110 transition-all flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isChangingPassword ? (
                        <>
                          <span className="material-symbols-outlined animate-spin text-[16px]">sync</span>
                          Updating Password...
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-[16px]">security</span>
                          Update Password
                        </>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>

            {/* Tactical RBAC Permission Matrix (Derived from real backend role) */}
            <div className="bg-surface-container-lowest p-space-md rounded-lg border border-outline-variant/30 mb-space-md">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold">
                  Tactical RBAC Access Rights
                </span>
                <span className="font-mono-data text-[10px] uppercase font-bold text-secondary">
                  Active Tier: {profile.role}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[12px]">
                <div className="flex items-center justify-between p-2 rounded bg-surface-container/60">
                  <span>Demand Review & Override</span>
                  <span className={isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'}>
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'READ-ONLY'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-surface-container/60">
                  <span>OR-Tools Solver Dispatch</span>
                  <span className={isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'}>
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'LOCKED'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-surface-container/60">
                  <span>Relief Allocation Drafting</span>
                  <span className={isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'}>
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'LOCKED'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded bg-surface-container/60">
                  <span>System Mode Switch & Drills</span>
                  <span className={isCommander ? 'text-amber-400 font-mono-data font-bold' : 'text-outline font-mono-data'}>
                    {isCommander ? 'COMMANDER ONLY' : 'LOCKED'}
                  </span>
                </div>
              </div>
            </div>

            {/* Preferences Toggles */}
            <div className="space-y-2 mb-space-md">
              <label className="flex items-center justify-between p-2 rounded bg-surface-container cursor-pointer hover:bg-surface-container-high transition-colors">
                <span className="text-[12px] text-on-surface">Show ISO-19115 Data Provenance Badges</span>
                <input
                  type="checkbox"
                  checked={showBadges}
                  onChange={(e) => setShowBadges(e.target.checked)}
                  className="accent-primary w-4 h-4 rounded cursor-pointer"
                />
              </label>
              <label className="flex items-center justify-between p-2 rounded bg-surface-container cursor-pointer hover:bg-surface-container-high transition-colors">
                <span className="text-[12px] text-on-surface">Auditory Flood Surge Alerts (Tactical Chime)</span>
                <input
                  type="checkbox"
                  checked={auditoryAlerts}
                  onChange={(e) => setAuditoryAlerts(e.target.checked)}
                  className="accent-primary w-4 h-4 rounded cursor-pointer"
                />
              </label>
            </div>
          </>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-outline-variant/30 pt-3 mt-auto">
          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-1.5 rounded bg-error/10 hover:bg-error/20 text-error border border-error/30 text-[11px] font-semibold flex items-center gap-1 transition-colors"
            title="Terminate Active Officer Shift"
          >
            <span className="material-symbols-outlined text-[15px]">logout</span>
            End Shift / Logout
          </button>
          <div className="flex items-center gap-3">
            <span className="font-mono-data text-[10px] text-outline hidden sm:inline">
              Session: SECURE_HMAC_SHA256
            </span>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 transition-all shadow-sm"
            >
              Close Dossier
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
