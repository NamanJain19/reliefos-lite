import React, { useState, useEffect, useRef } from 'react';
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

  // Photo state
  const [previewAvatarUrl, setPreviewAvatarUrl] = useState<string | null>(null);
  const [pendingAvatarDataUrl, setPendingAvatarDataUrl] = useState<string | null>(null);
  const [isPhotoModified, setIsPhotoModified] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeBlobUrlRef = useRef<string | null>(null);

  // Password change state
  const [isPasswordSectionOpen, setIsPasswordSectionOpen] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // Export state
  const [isExporting, setIsExporting] = useState(false);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Preference toggles
  const [showBadges, setShowBadges] = useState(true);
  const [auditoryAlerts, setAuditoryAlerts] = useState(true);

  // Cleanup blob URLs on unmount or reset
  const cleanupBlobUrl = () => {
    if (activeBlobUrlRef.current) {
      URL.revokeObjectURL(activeBlobUrlRef.current);
      activeBlobUrlRef.current = null;
    }
  };

  // Load user profile from persistent backend database
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
        setPreviewAvatarUrl(null);
        setPendingAvatarDataUrl(null);
        setIsPhotoModified(false);
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
    } else {
      cleanupBlobUrl();
    }
  }, [isOpen]);

  useEffect(() => {
    return () => {
      cleanupBlobUrl();
    };
  }, []);

  if (!isOpen) return null;

  // Handle Edit Mode Toggle
  const handleStartEdit = () => {
    setFormData({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      agency: profile.agency || '',
    });
    setPreviewAvatarUrl(null);
    setPendingAvatarDataUrl(null);
    setIsPhotoModified(false);
    setStatusMessage(null);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    cleanupBlobUrl();
    setFormData({
      name: profile.name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      agency: profile.agency || '',
    });
    setPreviewAvatarUrl(null);
    setPendingAvatarDataUrl(null);
    setIsPhotoModified(false);
    setStatusMessage(null);
    setIsEditing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Trigger File Input Picker
  const handleTriggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  // Handle Local Photo Selection with Instant 0ms Preview & Validation
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStatusMessage(null);
    const file = e.target.files?.[0];
    if (!file) return;

    // 1. Format validation: JPG, PNG, WebP
    const validMimes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validMimes.includes(file.type.toLowerCase())) {
      setStatusMessage({
        type: 'error',
        text: 'Unsupported image format. Allowed formats: JPG, PNG, or WebP.',
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // 2. Size validation: Max 2MB (2,097,152 bytes)
    const MAX_BYTES = 2 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      const actualMb = (file.size / (1024 * 1024)).toFixed(2);
      setStatusMessage({
        type: 'error',
        text: `File size exceeds 2MB limit (Selected: ${actualMb} MB). Please choose a compressed photo.`,
      });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // 3. Instant local preview via Blob URL (0ms lag, no round trip)
    cleanupBlobUrl();
    const objectUrl = URL.createObjectURL(file);
    activeBlobUrlRef.current = objectUrl;
    setPreviewAvatarUrl(objectUrl);
    setIsPhotoModified(true);

    // If not already in edit mode, activate edit mode so user can save or cancel the photo
    if (!isEditing) {
      setFormData({
        name: profile.name || '',
        email: profile.email || '',
        phone: profile.phone || '',
        agency: profile.agency || '',
      });
      setIsEditing(true);
    }

    // 4. Asynchronously read base64 data URI for database persistence
    const reader = new FileReader();
    reader.onload = () => {
      setPendingAvatarDataUrl(reader.result as string);
    };
    reader.onerror = () => {
      setStatusMessage({
        type: 'error',
        text: 'Failed to read image file. Please verify file integrity and try again.',
      });
      cleanupBlobUrl();
      setPreviewAvatarUrl(null);
      setPendingAvatarDataUrl(null);
      setIsPhotoModified(false);
    };
    reader.readAsDataURL(file);
  };

  // Handle Photo Removal (Reset to Default Avatar)
  const handleRemovePhoto = () => {
    cleanupBlobUrl();
    const defaultAvatar = '/officer_sharma.png';
    setPreviewAvatarUrl(defaultAvatar);
    setPendingAvatarDataUrl(defaultAvatar);
    setIsPhotoModified(true);
    if (!isEditing) {
      setIsEditing(true);
    }
    setStatusMessage({
      type: 'success',
      text: 'Default operational avatar selected. Click "Save Changes" to commit.',
    });
  };

  // Validate and Save Profile (persists to backend database)
  const handleSaveProfile = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setStatusMessage(null);

    // Validation
    const trimmedName = formData.name.trim();
    if (trimmedName.length < 2) {
      setStatusMessage({ type: 'error', text: 'Full Officer Name must be at least 2 characters long.' });
      return;
    }

    const trimmedEmail = formData.email.trim();
    if (trimmedEmail && (!trimmedEmail.includes('@') || !trimmedEmail.split('@')[1]?.includes('.'))) {
      setStatusMessage({ type: 'error', text: 'Please enter a valid official email address.' });
      return;
    }

    setIsSaving(true);
    try {
      const payload: any = {
        name: trimmedName,
        email: trimmedEmail,
        phone: formData.phone.trim(),
        agency: formData.agency.trim(),
      };

      // Include avatar if modified
      if (isPhotoModified && pendingAvatarDataUrl) {
        payload.avatar_url = pendingAvatarDataUrl;
      }

      const updated = await api.updateProfile(payload);

      setProfile(updated);
      cleanupBlobUrl();
      setPreviewAvatarUrl(null);
      setPendingAvatarDataUrl(null);
      setIsPhotoModified(false);
      setIsEditing(false);

      setStatusMessage({
        type: 'success',
        text: 'Officer dossier successfully updated and persisted in ASDMA registry.',
      });

      // Notify Topbar, Sidebar, and other application components
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

  // Handle Export Dossier (Signed Cryptographic JSON & Clean Printable PDF Window)
  const handleExportDossier = async (format: 'json' | 'print' = 'json') => {
    setIsExporting(true);
    setStatusMessage(null);

    try {
      const dossier = await api.exportDossier();

      if (format === 'json') {
        // Machine-readable cryptographically verified JSON export
        const jsonBlob = new Blob([JSON.stringify(dossier, null, 2)], { type: 'application/json' });
        const downloadUrl = URL.createObjectURL(jsonBlob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `ASDMA_Officer_Dossier_${profile.username.toUpperCase()}_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);

        setStatusMessage({
          type: 'success',
          text: `Official Duty Dossier JSON exported with SHA-256 integrity hash: ${dossier.cryptographic_hash_sha256?.substring(0, 12)}...`,
        });
      } else {
        // Printable / PDF Document Dossier View
        const printWindow = window.open('', '_blank');
        if (printWindow) {
          const avatarSrc = profile.avatar_url || '/officer_sharma.png';
          printWindow.document.write(`
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <title>ASDMA Officer Duty Dossier — ${profile.name}</title>
              <style>
                body {
                  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                  background: #ffffff;
                  color: #111827;
                  padding: 40px;
                  margin: 0;
                  line-height: 1.5;
                }
                .header {
                  border-bottom: 2px solid #0284c7;
                  padding-bottom: 16px;
                  margin-bottom: 24px;
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                }
                .badge {
                  background: #e0f2fe;
                  color: #0369a1;
                  padding: 4px 10px;
                  border-radius: 4px;
                  font-size: 12px;
                  font-weight: 700;
                  text-transform: uppercase;
                  letter-spacing: 0.05em;
                }
                .profile-card {
                  display: flex;
                  gap: 24px;
                  align-items: center;
                  background: #f8fafc;
                  border: 1px solid #e2e8f0;
                  border-radius: 8px;
                  padding: 20px;
                  margin-bottom: 24px;
                }
                .avatar {
                  width: 90px;
                  height: 90px;
                  border-radius: 8px;
                  border: 2px solid #0284c7;
                  object-fit: cover;
                }
                table {
                  width: 100%;
                  border-collapse: collapse;
                  margin-bottom: 24px;
                }
                th, td {
                  padding: 10px 14px;
                  border: 1px solid #e2e8f0;
                  font-size: 13px;
                  text-align: left;
                }
                th {
                  background: #f1f5f9;
                  color: #475569;
                  font-weight: 600;
                  width: 30%;
                }
                .capabilities-grid {
                  display: grid;
                  grid-template-columns: 1fr 1fr;
                  gap: 8px;
                  margin-top: 12px;
                }
                .cap-item {
                  background: #f1f5f9;
                  padding: 6px 10px;
                  border-radius: 4px;
                  font-size: 12px;
                  font-family: monospace;
                  border-left: 3px solid #0284c7;
                }
                .footer {
                  margin-top: 36px;
                  border-top: 1px solid #e2e8f0;
                  padding-top: 16px;
                  font-size: 11px;
                  color: #64748b;
                  font-family: monospace;
                }
                @media print {
                  body { padding: 20px; }
                  .no-print { display: none; }
                }
              </style>
            </head>
            <body>
              <div class="header">
                <div>
                  <h1 style="margin: 0; font-size: 20px; color: #0f172a;">ASSAM STATE DISASTER MANAGEMENT AUTHORITY</h1>
                  <p style="margin: 4px 0 0; font-size: 12px; color: #64748b; font-family: monospace;">INCIDENT COMMAND PROTOCOL • OPERATIONAL DUTY DOSSIER</p>
                </div>
                <div class="badge">ACTIVE TIER: ${profile.role}</div>
              </div>

              <div class="profile-card">
                <img src="${avatarSrc}" alt="${profile.name}" class="avatar" />
                <div>
                  <h2 style="margin: 0 0 4px; font-size: 18px; color: #0f172a;">${profile.name}</h2>
                  <p style="margin: 0 0 4px; font-size: 12px; color: #0284c7; font-family: monospace; font-weight: 600;">ID: ASDMA-EMP-8841-${profile.username.toUpperCase()}</p>
                  <p style="margin: 0; font-size: 13px; color: #475569;">Duty Station: ${profile.agency || 'Kamrup Metro Logistics Desk'}</p>
                </div>
              </div>

              <h3 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; margin-bottom: 8px;">1. Operational Identification Dossier</h3>
              <table>
                <tr><th>Official Name</th><td>${profile.name}</td></tr>
                <tr><th>Username</th><td>@${profile.username}</td></tr>
                <tr><th>Official Email</th><td>${profile.email || 'N/A'}</td></tr>
                <tr><th>Contact Phone</th><td>${profile.phone || 'N/A'}</td></tr>
                <tr><th>Assigned Logistics Desk</th><td>${profile.agency || 'Kamrup Metro District Control Room'}</td></tr>
                <tr><th>Jurisdiction Authority</th><td>Assam State Disaster Management Authority (ASDMA) • Kamrup Metropolitan EOC</td></tr>
              </table>

              <h3 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; margin-bottom: 8px;">2. Tactical RBAC Access Rights</h3>
              <p style="font-size: 12px; color: #64748b; margin: 0 0 8px;">Statutory Authority: Section 30, Disaster Management Act 2005</p>
              <div class="capabilities-grid">
                ${(dossier.rbac_governance?.authorized_capabilities || ['READ_TELEMETRY', 'VIEW_GIS_MAP'])
                  .map((cap: string) => `<div class="cap-item">✓ ${cap}</div>`)
                  .join('')}
              </div>

              <div class="footer">
                <p><strong>Cryptographic SHA-256 Hash:</strong> ${dossier.cryptographic_hash_sha256 || 'N/A'}</p>
                <p><strong>Generated At:</strong> ${dossier.generated_at || new Date().toISOString()} • <strong>Session Provenance:</strong> SECURE_HMAC_SHA256</p>
                <p>Statutory Notice: Official Government Disaster Relief Duty Record. Unauthorized duplication or credential tampering is prohibited under statutory emergency powers.</p>
              </div>

              <script>
                window.onload = function() {
                  window.print();
                };
              </script>
            </body>
            </html>
          `);
          printWindow.document.close();
          setStatusMessage({
            type: 'success',
            text: 'Printable Duty Dossier window prepared. Ready for PDF save or print.',
          });
        }
      }
    } catch (err: any) {
      const errDetail = err?.response?.data?.detail;
      const errMsg = typeof errDetail === 'string' ? errDetail : err?.message || 'Failed to export dossier.';
      setStatusMessage({ type: 'error', text: errMsg });
    } finally {
      setIsExporting(false);
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
    const parts = nameStr.replace(/^(Insp\.|Dr\.|Mr\.|Ms\.|Col\.|EOC)\s*/i, '').trim().split(/\s+/);
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return (parts[0]?.[0] || 'OP').toUpperCase();
  };

  // RBAC Permission checks based on real role
  const roleUpper = (profile.role || 'OPERATOR').toUpperCase();
  const isCommander = roleUpper === 'COMMANDER';
  const isOperatorOrCommander = roleUpper === 'COMMANDER' || roleUpper === 'OPERATOR';

  // Active display avatar (instant preview or current profile avatar)
  const currentDisplayAvatar = previewAvatarUrl || profile.avatar_url;

  return (
    <div className="fixed inset-0 z-[1200] flex items-start justify-end p-3 sm:p-4 pt-14 sm:pt-16 bg-black/75 backdrop-blur-sm animate-fadeIn">
      {/* Hidden File Input for Zero-Lag Photo Upload */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileSelect}
        className="hidden"
        aria-label="Upload profile photo"
      />

      <div className="bg-[#0e1d2c] border border-outline-variant/50 rounded-xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto p-4 sm:p-space-lg text-on-surface flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3 mb-space-md">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-primary text-[26px]">badge</span>
            <div>
              <h2 className="font-headline-sm text-[17px] sm:text-headline-sm font-bold tracking-tight text-on-surface">
                Operator Profile & Duty Dossier
              </h2>
              <span className="font-mono-data text-[10px] text-outline block leading-tight">
                ASDMA Incident Command Protocol • Assam State Disaster Management Authority
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface transition-colors"
            title="Close Dossier"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Status / Alert Banner */}
        {statusMessage && (
          <div
            className={`p-3 rounded-lg mb-space-md flex items-start gap-2.5 text-[12px] font-mono-data border animate-fadeIn ${
              statusMessage.type === 'success'
                ? 'bg-primary/10 border-primary/40 text-primary'
                : 'bg-error/10 border-error/40 text-error'
            }`}
          >
            <span className="material-symbols-outlined text-[18px] mt-0.5 flex-shrink-0">
              {statusMessage.type === 'success' ? 'check_circle' : 'error'}
            </span>
            <span className="flex-1 font-medium leading-relaxed">{statusMessage.text}</span>
            <button
              onClick={() => setStatusMessage(null)}
              className="hover:opacity-75 text-on-surface-variant p-0.5 flex-shrink-0"
              title="Dismiss"
            >
              <span className="material-symbols-outlined text-[14px]">close</span>
            </button>
          </div>
        )}

        {/* Loading Spinner for initial fetch */}
        {isLoading ? (
          <div className="p-10 flex flex-col items-center justify-center gap-2.5 text-outline">
            <span className="material-symbols-outlined animate-spin text-[32px] text-primary">sync</span>
            <span className="font-mono-data text-[12px]">Synchronizing officer records with ASDMA backend...</span>
          </div>
        ) : (
          <>
            {/* Officer Header Card (Responsive Layout, Zero-Clip Guarantee) */}
            <div className="bg-surface-container p-3 sm:p-4 rounded-xl border border-outline-variant/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 mb-space-md relative">
              <div className="flex items-center gap-3.5 min-w-0 flex-1">
                {/* Profile Photo / Avatar with Interactive Upload Trigger */}
                <div
                  onClick={handleTriggerFileInput}
                  className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl overflow-hidden border-2 border-primary/40 flex-shrink-0 bg-surface-container-high flex items-center justify-center relative group cursor-pointer shadow-md transition-all hover:border-primary"
                  title="Click to Change Photo (JPG, PNG, WebP • Max 2MB)"
                >
                  {currentDisplayAvatar ? (
                    <img
                      src={currentDisplayAvatar}
                      alt={profile.name}
                      className="w-full h-full object-cover object-center transition-transform duration-200 group-hover:scale-105"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : null}
                  <span className="font-mono-data font-bold text-[18px] sm:text-[20px] text-primary absolute pointer-events-none -z-0">
                    {getInitials(profile.name)}
                  </span>

                  {/* Hover Overlay with Camera Icon */}
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-[1px] flex flex-col items-center justify-center text-on-surface opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="material-symbols-outlined text-[20px] text-primary">photo_camera</span>
                    <span className="text-[9px] font-mono-data font-semibold text-primary tracking-wider mt-0.5">
                      CHANGE
                    </span>
                  </div>

                  {/* Active Preview Badge */}
                  {isPhotoModified && (
                    <span
                      className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-primary border-2 border-[#0e1d2c]"
                      title="Photo Modified (Preview Active)"
                    />
                  )}
                </div>

                {/* Officer Details & Badges */}
                <div className="flex flex-col min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-headline-sm text-[15px] sm:text-[17px] font-bold text-on-surface truncate">
                      {isEditing && formData.name ? formData.name : profile.name}
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

                  <span className="font-mono-data text-[11px] text-secondary/90 mt-1 leading-snug break-words">
                    ID: ASDMA-EMP-8841-{profile.username.toUpperCase()} • Duty:{' '}
                    {isEditing && formData.agency ? formData.agency : profile.agency || 'Kamrup Metro Logistics Desk'}
                  </span>

                  <span className="font-body-sm text-[11px] text-on-surface-variant truncate mt-0.5">
                    Official Contact: {isEditing && formData.email ? formData.email : profile.email || 'officer@asdma.gov.in'}
                    {' • '}
                    {isEditing && formData.phone ? formData.phone : profile.phone || '+91 94350 22002'}
                  </span>
                </div>
              </div>

              {/* Edit Mode Toggle Button */}
              {!isEditing ? (
                <button
                  type="button"
                  onClick={handleStartEdit}
                  className="px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-primary border border-primary/30 text-[12px] font-semibold flex items-center justify-center gap-1.5 transition-all self-start sm:self-center shadow-xs flex-shrink-0"
                  title="Edit Officer Profile"
                >
                  <span className="material-symbols-outlined text-[16px]">edit</span>
                  Edit Profile
                </button>
              ) : (
                <div className="px-2.5 py-1 rounded bg-primary/10 border border-primary/30 text-primary text-[11px] font-mono-data font-semibold flex items-center gap-1 self-start sm:self-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
                  EDIT MODE
                </div>
              )}
            </div>

            {/* Profile Fields Section: View Mode vs Edit Mode */}
            {isEditing ? (
              <form
                onSubmit={handleSaveProfile}
                className="bg-surface-container-lowest p-space-md rounded-xl border border-primary/30 mb-space-md space-y-3.5 shadow-inner"
              >
                <div className="flex items-center justify-between pb-1.5 border-b border-outline-variant/20">
                  <span className="font-label-sm text-[11px] uppercase tracking-wider text-primary font-bold flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[16px]">edit_note</span>
                    Edit Profile Details
                  </span>
                  <span className="font-mono-data text-[10px] text-outline">Database Persistence Enabled</span>
                </div>

                {/* Profile Photo Controls in Edit Mode */}
                <div className="p-3 rounded-lg bg-surface-container/50 border border-outline-variant/30 flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary text-[18px]">photo_camera</span>
                    <div className="text-[11px]">
                      <span className="font-semibold text-on-surface block">Profile Photo</span>
                      <span className="text-on-surface-variant text-[10.5px]">
                        {isPhotoModified ? 'Custom photo selected (preview active)' : 'JPG, PNG, or WebP up to 2MB'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleTriggerFileInput}
                      className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high text-primary border border-primary/30 text-[11px] font-medium flex items-center gap-1 transition-colors"
                    >
                      <span className="material-symbols-outlined text-[14px]">file_upload</span>
                      Change Photo
                    </button>
                    <button
                      type="button"
                      onClick={handleRemovePhoto}
                      className="px-2.5 py-1 rounded bg-surface-container hover:bg-error/20 text-error border border-error/30 text-[11px] font-medium flex items-center gap-1 transition-colors"
                      title="Reset to default ASDMA avatar"
                    >
                      <span className="material-symbols-outlined text-[14px]">delete</span>
                      Remove Photo
                    </button>
                  </div>
                </div>

                {/* Full Name Field */}
                <div>
                  <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                    Official Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    minLength={2}
                    placeholder="e.g. Insp. S. Sharma"
                    className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors font-medium"
                  />
                </div>

                {/* Email & Phone Fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="e.g. +91 94350 22002"
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors font-medium font-mono-data"
                    />
                  </div>
                </div>

                {/* Assigned Desk Field */}
                <div>
                  <label className="block text-[11px] font-mono-data uppercase text-outline mb-1 font-semibold">
                    Assigned Desk / Station
                  </label>
                  <input
                    type="text"
                    value={formData.agency}
                    onChange={(e) => setFormData({ ...formData, agency: e.target.value })}
                    placeholder="e.g. Kamrup Metro Logistics Desk"
                    className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors font-medium"
                  />
                </div>

                {/* RBAC Role - Strictly Read-Only with Security Notice */}
                <div className="p-2.5 rounded-lg bg-surface-container/60 border border-outline-variant/30 flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-[18px] text-amber-400 mt-0.5 flex-shrink-0">
                    lock
                  </span>
                  <div className="flex flex-col text-[11px]">
                    <span className="font-semibold text-on-surface flex items-center gap-1.5">
                      Role Tier: <span className="font-mono-data text-primary uppercase font-bold">{profile.role}</span>{' '}
                      (Protected)
                    </span>
                    <span className="text-on-surface-variant text-[10.5px] mt-0.5 leading-snug">
                      Operational role privileges, authorization levels, and usernames are strictly authoritative and
                      managed by District EOC Administration.
                    </span>
                  </div>
                </div>

                {/* Edit Form Action Buttons */}
                <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-outline-variant/20">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    disabled={isSaving}
                    className="px-3.5 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface text-[12px] font-medium transition-colors border border-outline-variant/40"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="px-4 py-1.5 rounded-lg bg-primary text-on-primary font-semibold text-[12px] hover:brightness-110 transition-all flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
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
              <div className="bg-surface-container-lowest p-space-md rounded-xl border border-outline-variant/30 mb-space-md">
                <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-outline-variant/20">
                  <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold">
                    Operational Identification Dossier
                  </span>
                  <span className="font-mono-data text-[10.5px] text-primary flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                    Verified ASDMA Record
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[12px]">
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
                    <span className="text-on-surface truncate block" title={profile.email}>
                      {profile.email || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">Contact Phone</span>
                    <span className="font-mono-data text-on-surface">{profile.phone || 'N/A'}</span>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-outline text-[10.5px] uppercase font-mono-data block">
                      Assigned Logistics Desk
                    </span>
                    <span className="text-on-surface">{profile.agency || 'Kamrup Metro District Control Room'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Password & Security Management Accordion */}
            <div className="bg-surface-container-lowest rounded-xl border border-outline-variant/30 mb-space-md overflow-hidden">
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
                <form
                  onSubmit={handleChangePassword}
                  className="p-space-md border-t border-outline-variant/20 space-y-3 bg-surface-container-low/50"
                >
                  <p className="text-[11px] text-on-surface-variant font-body-sm leading-tight">
                    Change your operational command password. Password requires verification of your current password
                    and a minimum of 6 characters.
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
                      className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                        className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
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
                        className="w-full px-3 py-1.5 rounded-lg bg-surface-container border border-outline-variant/50 text-on-surface text-[13px] focus:outline-none focus:border-primary transition-colors"
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
                      className="px-3 py-1.5 rounded-lg bg-surface-container text-on-surface-variant text-[12px] hover:text-on-surface transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isChangingPassword}
                      className="px-4 py-1.5 rounded-lg bg-secondary-container text-on-secondary-container font-semibold text-[12px] hover:brightness-110 transition-all flex items-center gap-1.5 disabled:opacity-50"
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
            <div className="bg-surface-container-lowest p-space-md rounded-xl border border-outline-variant/30 mb-space-md">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-sm text-[11px] uppercase tracking-wider text-outline font-semibold">
                  Tactical RBAC Access Rights
                </span>
                <span className="font-mono-data text-[10px] uppercase font-bold text-secondary">
                  Active Tier: {profile.role}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[12px]">
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-container/60">
                  <span>Demand Review & Override</span>
                  <span
                    className={
                      isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'
                    }
                  >
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'READ-ONLY'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-container/60">
                  <span>OR-Tools Solver Dispatch</span>
                  <span
                    className={
                      isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'
                    }
                  >
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'LOCKED'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-container/60">
                  <span>Relief Allocation Drafting</span>
                  <span
                    className={
                      isOperatorOrCommander ? 'text-primary font-mono-data font-bold' : 'text-outline font-mono-data'
                    }
                  >
                    {isOperatorOrCommander ? 'AUTHORIZED' : 'LOCKED'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-surface-container/60">
                  <span>System Mode Switch & Drills</span>
                  <span
                    className={
                      isCommander ? 'text-amber-400 font-mono-data font-bold' : 'text-outline font-mono-data'
                    }
                  >
                    {isCommander ? 'COMMANDER ONLY' : 'LOCKED'}
                  </span>
                </div>
              </div>
            </div>

            {/* Preferences Toggles */}
            <div className="space-y-2 mb-space-md">
              <label className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container cursor-pointer hover:bg-surface-container-high transition-colors">
                <span className="text-[12px] text-on-surface">Show ISO-19115 Data Provenance Badges</span>
                <input
                  type="checkbox"
                  checked={showBadges}
                  onChange={(e) => setShowBadges(e.target.checked)}
                  className="accent-primary w-4 h-4 rounded cursor-pointer"
                />
              </label>
              <label className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container cursor-pointer hover:bg-surface-container-high transition-colors">
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

        {/* Footer Actions: End Shift / Logout, Export Dossier & Close */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-t border-outline-variant/30 pt-3.5 mt-auto">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg bg-error/10 hover:bg-error/20 text-error border border-error/30 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors"
              title="Terminate Active Officer Shift"
            >
              <span className="material-symbols-outlined text-[15px]">logout</span>
              End Shift / Logout
            </button>

            {/* Genuine Export Dossier Button (JSON / Print) */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => handleExportDossier('json')}
                disabled={isExporting}
                className="px-3 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-secondary border border-secondary/30 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                title="Download verified cryptographic ASDMA JSON duty dossier"
              >
                {isExporting ? (
                  <span className="material-symbols-outlined animate-spin text-[15px]">sync</span>
                ) : (
                  <span className="material-symbols-outlined text-[15px]">download</span>
                )}
                Export Dossier
              </button>

              <button
                type="button"
                onClick={() => handleExportDossier('print')}
                disabled={isExporting}
                className="p-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container-highest text-on-surface-variant hover:text-on-surface border border-outline-variant/30 text-[11px] transition-colors disabled:opacity-50"
                title="Print / Save PDF Official Officer Dossier"
              >
                <span className="material-symbols-outlined text-[16px]">print</span>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between sm:justify-end gap-3">
            <span className="font-mono-data text-[10px] text-outline hidden md:inline">
              Session: SECURE_HMAC_SHA256
            </span>
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-4 py-1.5 rounded-lg bg-primary-container text-on-primary-container font-semibold text-[12px] hover:brightness-110 transition-all shadow-sm"
            >
              Close Dossier
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
