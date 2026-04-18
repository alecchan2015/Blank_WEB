<template>
  <router-view />
</template>

<style>
/* ═══════════════════════════════════════════════════════════════════
   Global design tokens + dark theme baseline
   Match Home.vue's aesthetic across all user-facing pages.
   Admin surface remains light (handled in admin/Layout.vue).
   ═══════════════════════════════════════════════════════════════════ */

:root {
  /* Dark surfaces */
  --ybc-bg:          #0a0a0f;
  --ybc-surface-1:   #12121a;
  --ybc-surface-2:   #1a1a24;
  --ybc-surface-3:   #22222e;
  --ybc-border:      rgba(255, 255, 255, 0.08);
  --ybc-border-hover:rgba(255, 255, 255, 0.14);

  /* Text */
  --ybc-text:        #e4e4e7;
  --ybc-text-strong: #ffffff;
  --ybc-text-dim:    #a1a1aa;
  --ybc-text-muted:  #71717a;
  --ybc-text-faint:  #52525b;

  /* Accents */
  --ybc-accent:       #6366f1;
  --ybc-accent-light: #818cf8;
  --ybc-accent-glow:  rgba(99, 102, 241, 0.25);
  --ybc-purple:       #a855f7;
  --ybc-pink:         #ec4899;
  --ybc-blue:         #3b82f6;
  --ybc-success:      #22c55e;
  --ybc-warning:      #f59e0b;
  --ybc-danger:       #ef4444;

  /* Gradients */
  --ybc-gradient-primary: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  --ybc-gradient-cool:    linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  --ybc-gradient-warm:    linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);

  /* Shadows */
  --ybc-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --ybc-shadow-md: 0 8px 24px rgba(0, 0, 0, 0.35);
  --ybc-shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.5);
  --ybc-glow:      0 0 0 1px rgba(99, 102, 241, 0.2), 0 8px 32px rgba(99, 102, 241, 0.15);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
               'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: var(--ybc-bg);
  color: var(--ybc-text);
  -webkit-font-smoothing: antialiased;
  -webkit-tap-highlight-color: transparent;
}

/* Keyboard focus — WCAG 2.1 AA accessibility */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[role="button"]:focus-visible {
  outline: 2px solid var(--ybc-accent, #6366f1);
  outline-offset: 2px;
  border-radius: 6px;
}
/* Mouse/touch interactions stay clean */
button:focus:not(:focus-visible),
a:focus:not(:focus-visible) { outline: none; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.18); }

/* ═══════════════════════════════════════════════════════════════════
   Element Plus — dark theme override (scoped to .ybc-dark ancestor)
   Admin pages stay light by not using the ybc-dark class.
   ═══════════════════════════════════════════════════════════════════ */

.ybc-dark {
  --el-color-primary:          #6366f1;
  --el-color-primary-light-3:  #818cf8;
  --el-color-primary-light-5:  rgba(99, 102, 241, 0.35);
  --el-color-primary-light-7:  rgba(99, 102, 241, 0.2);
  --el-color-primary-light-8:  rgba(99, 102, 241, 0.15);
  --el-color-primary-light-9:  rgba(99, 102, 241, 0.08);
  --el-color-primary-dark-2:   #4f46e5;

  --el-bg-color:                #12121a;
  --el-bg-color-page:           #0a0a0f;
  --el-bg-color-overlay:        #1a1a24;

  --el-text-color-primary:      #e4e4e7;
  --el-text-color-regular:      #a1a1aa;
  --el-text-color-secondary:    #71717a;
  --el-text-color-placeholder:  #52525b;
  --el-text-color-disabled:     #3f3f46;

  --el-border-color:            rgba(255, 255, 255, 0.1);
  --el-border-color-light:      rgba(255, 255, 255, 0.08);
  --el-border-color-lighter:    rgba(255, 255, 255, 0.06);
  --el-border-color-extra-light:rgba(255, 255, 255, 0.04);

  --el-fill-color:              rgba(255, 255, 255, 0.04);
  --el-fill-color-light:        rgba(255, 255, 255, 0.02);
  --el-fill-color-lighter:      rgba(255, 255, 255, 0.02);
  --el-fill-color-blank:        transparent;
}

/* ── Element Plus component overrides in dark mode ── */

.ybc-dark .el-card,
.ybc-dark .el-card.is-always-shadow,
.ybc-dark .el-card.is-never-shadow {
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
  color: var(--ybc-text);
  box-shadow: var(--ybc-shadow-sm);
}
.ybc-dark .el-card:hover { border-color: var(--ybc-border-hover); }
.ybc-dark .el-card__header { border-bottom-color: var(--ybc-border); color: var(--ybc-text-strong); }

.ybc-dark .el-input__wrapper,
.ybc-dark .el-textarea__inner,
.ybc-dark .el-input-number__decrease,
.ybc-dark .el-input-number__increase {
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 0 0 1px var(--ybc-border) inset;
  color: var(--ybc-text);
}
.ybc-dark .el-input__inner,
.ybc-dark .el-textarea__inner {
  color: var(--ybc-text) !important;
  -webkit-text-fill-color: var(--ybc-text);
}
.ybc-dark .el-input__wrapper.is-focus,
.ybc-dark .el-textarea__inner:focus {
  box-shadow: 0 0 0 1px var(--ybc-accent) inset !important;
}
.ybc-dark .el-input__inner::placeholder,
.ybc-dark .el-textarea__inner::placeholder {
  color: var(--ybc-text-faint);
}

.ybc-dark .el-select__wrapper {
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 0 0 1px var(--ybc-border) inset;
  color: var(--ybc-text);
}
.ybc-dark .el-select-dropdown {
  background: var(--ybc-surface-2);
  border-color: var(--ybc-border);
}
.ybc-dark .el-select-dropdown__item.is-hovering,
.ybc-dark .el-select-dropdown__item:hover {
  background: rgba(99, 102, 241, 0.12);
  color: var(--ybc-text-strong);
}
.ybc-dark .el-select-dropdown__item.is-selected {
  color: var(--ybc-accent-light);
  background: rgba(99, 102, 241, 0.08);
}

.ybc-dark .el-button {
  background: var(--ybc-surface-2);
  border-color: var(--ybc-border);
  color: var(--ybc-text);
}
.ybc-dark .el-button:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: var(--ybc-accent-light);
  color: var(--ybc-text-strong);
}
.ybc-dark .el-button--primary {
  background: var(--ybc-accent);
  border-color: var(--ybc-accent);
  color: #ffffff;
}
.ybc-dark .el-button--primary:hover {
  background: var(--ybc-accent-light);
  border-color: var(--ybc-accent-light);
}
.ybc-dark .el-button--text,
.ybc-dark .el-button.is-text,
.ybc-dark .el-button.is-link {
  background: transparent;
  border-color: transparent;
}

.ybc-dark .el-tag {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.25);
  color: var(--ybc-accent-light);
}
.ybc-dark .el-tag--success {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.25);
  color: #86efac;
}
.ybc-dark .el-tag--warning {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.25);
  color: #fcd34d;
}
.ybc-dark .el-tag--danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.25);
  color: #fca5a5;
}
.ybc-dark .el-tag--info {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--ybc-border);
  color: var(--ybc-text-dim);
}

.ybc-dark .el-menu {
  background: transparent;
  border-right: 0;
}
.ybc-dark .el-menu-item {
  color: var(--ybc-text-dim);
}
.ybc-dark .el-menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--ybc-text-strong);
}
.ybc-dark .el-menu-item.is-active {
  background: rgba(99, 102, 241, 0.12) !important;
  color: var(--ybc-accent-light) !important;
  box-shadow: inset 2px 0 0 var(--ybc-accent);
}

.ybc-dark .el-alert {
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: var(--ybc-text);
}
.ybc-dark .el-alert--info  { background: rgba(99, 102, 241, 0.08); border-color: rgba(99, 102, 241, 0.2); }
.ybc-dark .el-alert--success { background: rgba(34, 197, 94, 0.08); border-color: rgba(34, 197, 94, 0.2); }
.ybc-dark .el-alert--warning { background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.2); }
.ybc-dark .el-alert--error { background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.2); }
.ybc-dark .el-alert .el-alert__title,
.ybc-dark .el-alert .el-alert__description { color: var(--ybc-text); }

.ybc-dark .el-dialog {
  background: var(--ybc-surface-1);
  border: 1px solid var(--ybc-border);
}
.ybc-dark .el-dialog__title { color: var(--ybc-text-strong); }
.ybc-dark .el-dialog__body { color: var(--ybc-text); }

.ybc-dark .el-form-item__label { color: var(--ybc-text-dim); }

.ybc-dark .el-empty__description { color: var(--ybc-text-muted); }

.ybc-dark .el-divider { border-color: var(--ybc-border); }
.ybc-dark .el-divider__text {
  background: var(--ybc-bg);
  color: var(--ybc-text-dim);
}

.ybc-dark .el-switch__core { background: rgba(255, 255, 255, 0.1); border-color: var(--ybc-border); }
.ybc-dark .el-switch.is-checked .el-switch__core { background: var(--ybc-accent); border-color: var(--ybc-accent); }

.ybc-dark .el-progress-bar__outer { background: rgba(255, 255, 255, 0.06); }
.ybc-dark .el-progress-bar__inner { background: var(--ybc-gradient-primary); }
.ybc-dark .el-progress__text { color: var(--ybc-text-dim); }

.ybc-dark .el-skeleton { background: transparent; }
.ybc-dark .el-skeleton__item {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.04) 25%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.04) 75%
  );
  background-size: 200% 100%;
}

/* Utility animation classes used across dark pages */
@keyframes ybc-pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
@keyframes ybc-fade-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
