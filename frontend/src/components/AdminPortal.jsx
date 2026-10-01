import React, { useState, useEffect, useCallback } from "react";
import {
  Plus, Edit, Trash2, Calendar, Users, Building, CheckCircle, Clock,
  XCircle, Search, RefreshCw, AlertCircle, ArrowUpRight, Flame, Mail,
  Phone, Sparkles, Send, Copy, Eye, Check, X, ShieldAlert, CheckCircle2, ChevronRight
} from "lucide-react";
import { formatPKR } from "./PropertyCard";

export default function AdminPortal({ onRefreshStats, initialTab = "properties" }) {
  const [activeAdminTab, setActiveAdminTab] = useState(initialTab); // "properties" | "schedules" | "leads" | "voice-leads"

  useEffect(() => {
    if (initialTab) setActiveAdminTab(initialTab);
  }, [initialTab]);
  
  // Properties state
  const [properties, setProperties] = useState([]);
  const [totalProps, setTotalProps] = useState(0);
  const [search, setSearch] = useState("");
  const [propPage, setPropPage] = useState(1);
  const [loadingProps, setLoadingProps] = useState(false);

  // Appointments state
  const [appointments, setAppointments] = useState([]);
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState({});
  const [loadingCRM, setLoadingCRM] = useState(false);

  // Voice Call Lead Scoring & VIP Alerts state (Task 4)
  const [voiceLeads, setVoiceLeads] = useState([]);
  const [voiceStats, setVoiceStats] = useState({});
  const [loadingVoice, setLoadingVoice] = useState(false);
  const [voiceFilter, setVoiceFilter] = useState("all"); // "all" | "hot" | "warm" | "cold"
  const [voiceSearch, setVoiceSearch] = useState("");
  const [selectedEmailAlert, setSelectedEmailAlert] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [simulationSuccessMsg, setSimulationSuccessMsg] = useState("");

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editProperty, setEditProperty] = useState(null);
  const [rescheduleAppt, setRescheduleAppt] = useState(null);
  const [cancelAppt, setCancelAppt] = useState(null);

  // Form inputs for Add/Edit
  const [formProp, setFormProp] = useState({
    property_id: "",
    property_type: "House",
    purpose: "For Sale",
    city: "Lahore",
    locality: "DHA Phase 6",
    location: "DHA Phase 6, Lahore",
    price: 28500000,
    area_marla: 5,
    bedrooms: 3,
    baths: 3,
    agent: "Ahmed Raza (Sahi RealEstate)",
  });

  // Reschedule Form
  const [newDate, setNewDate] = useState("Tomorrow");
  const [newTime, setNewTime] = useState("4:00 PM");
  const [reschedNotes, setReschedNotes] = useState("");
  const [cancelReason, setCancelReason] = useState("");

  const fetchProperties = useCallback(async () => {
    setLoadingProps(true);
    try {
      const res = await fetch(`/api/properties?page=${propPage}&limit=10&search=${encodeURIComponent(search)}`);
      const data = await res.json();
      if (data.ok) {
        setProperties(data.properties || []);
        setTotalProps(data.total || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingProps(false);
    }
  }, [propPage, search]);

  const fetchCRMData = useCallback(async () => {
    setLoadingCRM(true);
    try {
      const [apptsRes, leadsRes, statsRes] = await Promise.all([
        fetch("/api/crm/appointments").then((r) => r.json()),
        fetch("/api/crm/leads").then((r) => r.json()),
        fetch("/api/crm/stats").then((r) => r.json()),
      ]);
      if (apptsRes.ok) setAppointments(apptsRes.appointments || []);
      if (leadsRes.ok) setLeads(leadsRes.leads || []);
      if (statsRes.ok) setStats(statsRes.stats || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCRM(false);
    }
  }, []);

  const fetchVoiceLeads = useCallback(async () => {
    setLoadingVoice(true);
    try {
      const res = await fetch("/api/crm/voice-leads?limit=50");
      const data = await res.json();
      if (data.ok) {
        setVoiceLeads(data.voice_leads || []);
        setVoiceStats(data.stats || {});
      }
    } catch (err) {
      console.error("Failed to fetch voice leads:", err);
    } finally {
      setLoadingVoice(false);
    }
  }, []);

  const handleSimulateCall = async (type) => {
    setSimulating(true);
    setSimulationSuccessMsg("");
    try {
      const res = await fetch("/api/crm/voice-leads/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type }),
      });
      const data = await res.json();
      if (data.ok) {
        await fetchVoiceLeads();
        const isHot = data.lead_score?.tier === "Hot";
        setSimulationSuccessMsg(
          isHot
            ? `🔥 Hot Lead simulated! Score: ${data.lead_score.conversion_score_pct}%. VIP alert email dispatched to ${data.lead_score.assigned_employee_email || 'closer.vip@realestatehub.pk'}.`
            : `⚡ Warm Lead simulated! Score: ${data.lead_score.conversion_score_pct}%. Added to nurture pipeline.`
        );
        if (isHot && data.email_body) {
          setSelectedEmailAlert({
            call_id: data.call_id,
            caller_id: "+923009988112",
            conversion_score_pct: data.lead_score.conversion_score_pct,
            tier: "Hot",
            customer_persona: data.lead_score.customer_persona,
            assigned_employee_email: data.lead_score.assigned_employee_email || "closer.vip@realestatehub.pk",
            email_subject: data.email_subject || `🚨 [VIP HOT LEAD] ${data.call_id}`,
            email_body: data.email_body,
            created_at: new Date().toISOString(),
          });
        }
      }
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  useEffect(() => {
    fetchProperties();
  }, [fetchProperties]);

  useEffect(() => {
    fetchCRMData();
  }, [fetchCRMData]);

  useEffect(() => {
    fetchVoiceLeads();
  }, [fetchVoiceLeads]);

  // Handle Add Property
  const handleSaveAdd = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/properties", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formProp),
      });
      const data = await res.json();
      if (data.ok) {
        setShowAddModal(false);
        fetchProperties();
        fetchCRMData();
        if (onRefreshStats) onRefreshStats();
      } else {
        alert(data.error || "Failed to add property");
      }
    } catch (err) {
      alert("Error adding property: " + err.message);
    }
  };

  // Handle Edit Property
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editProperty) return;
    try {
      const res = await fetch(`/api/properties/${editProperty.property_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editProperty),
      });
      const data = await res.json();
      if (data.ok) {
        setEditProperty(null);
        fetchProperties();
      } else {
        alert(data.error || "Failed to edit property");
      }
    } catch (err) {
      alert("Error updating property: " + err.message);
    }
  };

  // Handle Delete Property
  const handleDelete = async (pid) => {
    if (!window.confirm(`Are you sure you want to delete property ${pid}?`)) return;
    try {
      await fetch(`/api/properties/${pid}`, { method: "DELETE" });
      fetchProperties();
      fetchCRMData();
    } catch (err) {
      alert("Error deleting: " + err.message);
    }
  };

  // Handle Reschedule Appointment
  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!rescheduleAppt) return;
    try {
      await fetch(`/api/crm/appointments/${rescheduleAppt.appointment_id}/reschedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date_str: newDate,
          time_str: newTime,
          notes: reschedNotes || "Rescheduled via Admin CRM",
        }),
      });
      setRescheduleAppt(null);
      fetchCRMData();
    } catch (err) {
      alert("Error rescheduling: " + err.message);
    }
  };

  // Handle Cancel Appointment
  const handleCancelSubmit = async (e) => {
    e.preventDefault();
    if (!cancelAppt) return;
    try {
      await fetch(`/api/crm/appointments/${cancelAppt.appointment_id}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: cancelReason || "Cancelled by admin" }),
      });
      setCancelAppt(null);
      fetchCRMData();
    } catch (err) {
      alert("Error cancelling: " + err.message);
    }
  };

  return (
    <div className="py-8 px-4 sm:px-8 max-w-7xl mx-auto">
      {/* Top Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-8">
        <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10 flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
            <Building className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-heading font-extrabold text-white">{stats.total_properties || totalProps}</div>
            <div className="text-xs text-slate-400">Total Properties</div>
          </div>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10 flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-cyan-500/15 text-cyan-400 border border-cyan-500/20">
            <Calendar className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-heading font-extrabold text-white">{stats.total_appointments || appointments.length}</div>
            <div className="text-xs text-slate-400">Total Visits Booked</div>
          </div>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10 flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/20">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-heading font-extrabold text-white">{stats.scheduled_appointments || 0}</div>
            <div className="text-xs text-slate-400">Scheduled / Active</div>
          </div>
        </div>

        <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10 flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-purple-500/15 text-purple-400 border border-purple-500/20">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-heading font-extrabold text-white">{stats.total_leads || leads.length}</div>
            <div className="text-xs text-slate-400">CRM Client Leads</div>
          </div>
        </div>

        <div
          onClick={() => setActiveAdminTab("voice-leads")}
          className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-red-500/20 hover:border-red-500/50 transition-all cursor-pointer flex items-center gap-3.5 group shadow-sm hover:shadow-red-950/20"
          title="Click to view automated voice call scoring and VIP hot alerts"
        >
          <div className="p-3 rounded-xl bg-red-500/15 text-red-400 border border-red-500/30 group-hover:scale-105 transition-transform">
            <Flame className="w-5 h-5 text-red-400 animate-pulse" />
          </div>
          <div>
            <div className="text-xl font-heading font-extrabold text-white flex items-center gap-1.5">
              <span>{voiceStats.total_calls_scored || voiceLeads.length}</span>
              {voiceStats.hot_leads_count > 0 && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/25 text-red-300 font-bold border border-red-500/40">
                  {voiceStats.hot_leads_count} Hot
                </span>
              )}
            </div>
            <div className="text-xs text-slate-400 group-hover:text-red-300 transition-colors">Voice Scored Leads</div>
          </div>
        </div>
      </div>

      {/* Admin Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 pb-4 border-b border-white/10">
        <div className="flex flex-wrap bg-slate-900/80 p-1 rounded-xl border border-white/10 gap-1">
          <button
            onClick={() => setActiveAdminTab("properties")}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeAdminTab === "properties"
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            Properties ({totalProps})
          </button>
          <button
            onClick={() => setActiveAdminTab("schedules")}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeAdminTab === "schedules"
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            Visit Schedules ({appointments.length})
          </button>
          <button
            onClick={() => setActiveAdminTab("leads")}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeAdminTab === "leads"
                ? "bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            CRM Pipeline ({leads.length})
          </button>
          <button
            onClick={() => setActiveAdminTab("voice-leads")}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeAdminTab === "voice-leads"
                ? "bg-gradient-to-r from-red-600 to-amber-500 text-white font-bold shadow-md shadow-red-600/30"
                : "text-red-300/80 hover:text-white"
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-amber-300" />
            <span>Voice Lead Scoring & Alerts ({voiceLeads.length})</span>
            {voiceStats.hot_leads_count > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[9px] bg-red-700 text-white font-extrabold shadow-sm">
                {voiceStats.hot_leads_count} HOT
              </span>
            )}
          </button>
        </div>

        {activeAdminTab === "properties" && (
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary text-xs py-2 px-3.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold border-amber-400/30"
          >
            <Plus className="w-4 h-4" />
            Add New Property
          </button>
        )}
      </div>

      {/* Tab 1: Properties Management */}
      {activeAdminTab === "properties" && (
        <div className="glass-panel p-5 bg-slate-900/80 rounded-2xl border border-white/10 overflow-hidden">
          <div className="flex items-center justify-between gap-4 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPropPage(1); }}
                placeholder="Filter listings by ID, locality, city..."
                className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-slate-950/70 border border-white/10 text-white text-xs focus:outline-none focus:border-amber-500"
              />
            </div>
            <button
              onClick={fetchProperties}
              className="btn-secondary text-xs py-1.5 px-3 rounded-lg"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/70 text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <tr>
                  <th className="p-3">ID</th>
                  <th className="p-3">Type / Purpose</th>
                  <th className="p-3">Locality & City</th>
                  <th className="p-3">Price</th>
                  <th className="p-3">Area / Beds</th>
                  <th className="p-3">Assigned Agent</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {properties.map((p) => (
                  <tr key={p.property_id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-mono font-bold text-amber-400">{p.property_id}</td>
                    <td className="p-3">
                      <span className="font-semibold text-white">{p.property_type}</span>
                      <span className="text-[10px] block text-slate-400">{p.purpose}</span>
                    </td>
                    <td className="p-3">
                      <div className="text-white font-medium">{p.locality}</div>
                      <div className="text-[10px] text-slate-400">{p.city}</div>
                    </td>
                    <td className="p-3 font-bold text-emerald-400">{formatPKR(p.price)}</td>
                    <td className="p-3">
                      <div>{p.area_marla} Marla</div>
                      <div className="text-[10px] text-slate-400">{p.bedrooms} Beds • {p.baths} Baths</div>
                    </td>
                    <td className="p-3 text-slate-300 truncate max-w-[140px]">{p.agent}</td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setEditProperty({ ...p })}
                          className="p-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 transition-colors"
                          title="Edit Property"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(p.property_id)}
                          className="p-1.5 rounded-lg bg-red-500/15 hover:bg-red-500/25 text-red-300 transition-colors"
                          title="Delete Property"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
            <span>Page {propPage}</span>
            <div className="flex items-center gap-2">
              <button
                disabled={propPage <= 1}
                onClick={() => setPropPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 rounded bg-slate-800 disabled:opacity-30 hover:bg-slate-700"
              >
                Previous
              </button>
              <button
                disabled={properties.length < 10}
                onClick={() => setPropPage((p) => p + 1)}
                className="px-3 py-1 rounded bg-slate-800 disabled:opacity-30 hover:bg-slate-700"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: CRM Visit Schedules */}
      {activeAdminTab === "schedules" && (
        <div className="glass-panel p-5 bg-slate-900/80 rounded-2xl border border-white/10 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading font-bold text-base text-white">Client Site Visit Appointments</h3>
            <button onClick={fetchCRMData} className="btn-secondary text-xs py-1.5 px-3">
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh Schedules
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/70 text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <tr>
                  <th className="p-3">Appointment ID</th>
                  <th className="p-3">Client Details</th>
                  <th className="p-3">Target Property</th>
                  <th className="p-3">Date & Time</th>
                  <th className="p-3">Assigned Consultant</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {appointments.map((a) => (
                  <tr key={a.appointment_id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-mono text-cyan-400 font-semibold">{a.appointment_id}</td>
                    <td className="p-3">
                      <div className="text-white font-bold">{a.client_name}</div>
                      <div className="text-[10px] text-slate-400">{a.client_phone}</div>
                    </td>
                    <td className="p-3">
                      <div className="text-white font-medium truncate max-w-[180px]">{a.property_title}</div>
                      <div className="text-[10px] font-mono text-slate-400">{a.property_id}</div>
                    </td>
                    <td className="p-3">
                      <div className="text-emerald-400 font-semibold">{a.date_str}</div>
                      <div className="text-[10px] text-slate-400">{a.time_str}</div>
                    </td>
                    <td className="p-3 text-slate-300">{a.agent_name}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                        a.status === "scheduled"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : a.status === "rescheduled"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          : "bg-red-500/20 text-red-300 border border-red-500/30"
                      }`}>
                        {a.status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setRescheduleAppt(a);
                            setNewDate(a.date_str || "Tomorrow");
                            setNewTime(a.time_str || "4:00 PM");
                          }}
                          className="px-2 py-1 rounded bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 text-[11px] font-semibold"
                        >
                          Reschedule
                        </button>
                        {a.status !== "cancelled" && (
                          <button
                            onClick={() => setCancelAppt(a)}
                            className="px-2 py-1 rounded bg-red-500/15 hover:bg-red-500/25 text-red-300 text-[11px] font-semibold"
                          >
                            Cancel
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: CRM Leads Pipeline */}
      {activeAdminTab === "leads" && (
        <div className="glass-panel p-5 bg-slate-900/80 rounded-2xl border border-white/10 overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-heading font-bold text-base text-white">Client Inquiry & Lead Pipeline</h3>
            <button onClick={fetchCRMData} className="btn-secondary text-xs py-1.5 px-3">
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh Leads
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/70 text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <tr>
                  <th className="p-3">Lead ID</th>
                  <th className="p-3">Client Name</th>
                  <th className="p-3">Contact</th>
                  <th className="p-3">City / Locality</th>
                  <th className="p-3">Budget</th>
                  <th className="p-3">Stage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {leads.map((l) => (
                  <tr key={l.lead_id} className="hover:bg-white/5 transition-colors">
                    <td className="p-3 font-mono text-purple-400">{l.lead_id}</td>
                    <td className="p-3 font-bold text-white">{l.client_name}</td>
                    <td className="p-3">
                      <div>{l.phone}</div>
                      <div className="text-[10px] text-slate-400">{l.email}</div>
                    </td>
                    <td className="p-3">{l.city || "Lahore"}</td>
                    <td className="p-3 font-semibold text-emerald-400">{l.budget || "Not Specified"}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        {l.stage || "Qualified"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Automated Post-Call Voice Lead Scoring & VIP Alerts (Task 4) */}
      {activeAdminTab === "voice-leads" && (
        <div className="space-y-6">
          {/* Notification banner for simulation */}
          {simulationSuccessMsg && (
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 text-amber-200 text-xs animate-in fade-in">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                <span>{simulationSuccessMsg}</span>
              </div>
              <button
                onClick={() => setSimulationSuccessMsg("")}
                className="text-amber-400 hover:text-white p-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Voice Intelligence Metrics Banner */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
            <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10">
              <div className="text-xs text-slate-400 mb-1 flex items-center justify-between">
                <span>Total Calls Scored</span>
                <Phone className="w-3.5 h-3.5 text-sky-400" />
              </div>
              <div className="text-2xl font-extrabold text-white">{voiceStats.total_calls_scored || voiceLeads.length}</div>
              <div className="text-[11px] text-slate-500 mt-1">LightGBM Machine Learning</div>
            </div>

            <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-red-500/30 bg-red-950/20">
              <div className="text-xs text-red-300 mb-1 flex items-center justify-between">
                <span>🔥 Hot Leads (SLA Alert)</span>
                <Flame className="w-3.5 h-3.5 text-red-400 animate-pulse" />
              </div>
              <div className="text-2xl font-extrabold text-red-400">{voiceStats.hot_leads_count || 0}</div>
              <div className="text-[11px] text-red-300/70 mt-1">Prob &ge; 70% • &lt;15 min SLA</div>
            </div>

            <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-amber-500/20">
              <div className="text-xs text-amber-300 mb-1 flex items-center justify-between">
                <span>⚡ Warm Leads</span>
                <Clock className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="text-2xl font-extrabold text-amber-400">{voiceStats.warm_leads_count || 0}</div>
              <div className="text-[11px] text-slate-500 mt-1">24h Follow-up Nurture</div>
            </div>

            <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-emerald-500/20">
              <div className="text-xs text-emerald-300 mb-1 flex items-center justify-between">
                <span>VIP Alerts Dispatched</span>
                <Mail className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <div className="text-2xl font-extrabold text-emerald-400">{voiceStats.vip_email_alerts_sent || 0}</div>
              <div className="text-[11px] text-emerald-400/70 mt-1">Direct to Sales Closer</div>
            </div>
          </div>

          {/* Interactive Toolbar */}
          <div className="glass-panel p-4 bg-slate-900/80 rounded-2xl border border-white/10 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-slate-400 mr-1">Filter Tier:</span>
                {["all", "hot", "warm", "cold"].map((t) => (
                  <button
                    key={t}
                    onClick={() => setVoiceFilter(t)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                      voiceFilter === t
                        ? t === "hot"
                          ? "bg-red-500 text-white font-bold shadow-md shadow-red-500/20"
                          : t === "warm"
                          ? "bg-amber-500 text-slate-950 font-bold"
                          : t === "cold"
                          ? "bg-slate-600 text-white font-bold"
                          : "bg-amber-400 text-slate-950 font-bold"
                        : "bg-slate-950/60 text-slate-300 hover:text-white border border-white/5"
                    }`}
                  >
                    {t === "all" ? `All (${voiceLeads.length})` : t}
                  </button>
                ))}
              </div>

              {/* Simulation One-Click Test Buttons */}
              <div className="flex items-center gap-2">
                <button
                  disabled={simulating}
                  onClick={() => handleSimulateCall("hot")}
                  className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white text-xs font-bold shadow-md shadow-red-600/20 flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
                  title="Simulate high-intent caller booking a visit in DHA Phase 6, triggering instant VIP hot alert email"
                >
                  <Flame className="w-3.5 h-3.5 text-yellow-300" />
                  <span>{simulating ? "Simulating..." : "⚡ Test Hot Lead Webhook"}</span>
                </button>

                <button
                  disabled={simulating}
                  onClick={() => handleSimulateCall("warm")}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
                  title="Simulate general inquiry caller"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Test Warm Call</span>
                </button>

                <button
                  onClick={fetchVoiceLeads}
                  className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/10"
                  title="Refresh Call List"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={voiceSearch}
                onChange={(e) => setVoiceSearch(e.target.value)}
                placeholder="Search by Call ID, Caller Phone (+92...), Society, Persona, or Action Plan..."
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950/80 border border-white/10 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-amber-400"
              />
            </div>
          </div>

          {/* Cards List of Scored Calls */}
          <div className="space-y-4">
            {voiceLeads
              .filter((vl) => {
                if (voiceFilter !== "all" && vl.tier?.toLowerCase() !== voiceFilter.toLowerCase()) {
                  return false;
                }
                if (!voiceSearch.trim()) return true;
                const q = voiceSearch.toLowerCase();
                return (
                  vl.call_id?.toLowerCase().includes(q) ||
                  vl.caller_id?.toLowerCase().includes(q) ||
                  vl.society?.toLowerCase().includes(q) ||
                  vl.city?.toLowerCase().includes(q) ||
                  vl.customer_persona?.toLowerCase().includes(q) ||
                  vl.transcript_summary?.toLowerCase().includes(q)
                );
              })
              .map((vl) => {
                const isHot = vl.tier === "Hot" || vl.hot_lead_alert_triggered;
                const isWarm = vl.tier === "Warm";
                return (
                  <div
                    key={vl.call_id}
                    className={`glass-panel p-5 bg-slate-900/90 rounded-2xl border transition-all ${
                      isHot
                        ? "border-red-500/40 shadow-[0_0_25px_rgba(239,68,68,0.12)] hover:border-red-500/60"
                        : "border-white/10 hover:border-white/20"
                    }`}
                  >
                    {/* Header */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-white/10 mb-3.5">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl flex items-center justify-center ${
                          isHot
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : isWarm
                            ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                            : "bg-slate-700/30 text-slate-400 border border-white/10"
                        }`}>
                          <Phone className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-heading font-extrabold text-sm text-white">{vl.caller_id}</span>
                            <span className="font-mono text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded-md border border-white/5">
                              {vl.call_id}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 mt-0.5">
                            Duration: <span className="text-white font-medium">{vl.duration_sec}s ({Math.round(vl.duration_sec / 60)} min)</span> • {vl.created_at ? new Date(vl.created_at).toLocaleString() : "Recent"}
                          </div>
                        </div>
                      </div>

                      {/* Tier Badge */}
                      <div>
                        {isHot ? (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-red-600/30 to-amber-600/30 border border-red-500/50 text-red-200 text-xs font-extrabold shadow-lg shadow-red-900/30 animate-pulse">
                            <Flame className="w-3.5 h-3.5 text-red-400" />
                            <span>🔥 HOT LEAD (High Intent)</span>
                          </div>
                        ) : isWarm ? (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-bold">
                            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                            <span>⚡ WARM LEAD</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-white/10 text-slate-400 text-xs font-medium">
                            <span>❄️ COLD LEAD</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Body Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4 text-xs">
                      {/* Column 1: Score & Persona */}
                      <div className="space-y-2.5 p-3 rounded-xl bg-slate-950/60 border border-white/5">
                        <div>
                          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                            <span>Conversion Probability</span>
                            <span className="font-extrabold text-white text-xs">{vl.conversion_score_pct}%</span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isHot
                                  ? "bg-gradient-to-r from-orange-500 to-red-500"
                                  : isWarm
                                  ? "bg-gradient-to-r from-amber-400 to-yellow-500"
                                  : "bg-slate-600"
                              }`}
                              style={{ width: `${Math.min(100, Math.max(10, vl.conversion_score_pct))}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <span className="text-[11px] text-slate-400 block mb-0.5">Assigned Customer Persona</span>
                          <span className="inline-block px-2 py-0.5 rounded-md bg-purple-500/15 text-purple-300 font-semibold border border-purple-500/20 text-[11px]">
                            {vl.customer_persona || "Standard Buyer"}
                          </span>
                        </div>
                      </div>

                      {/* Column 2: Parameters */}
                      <div className="space-y-1.5 p-3 rounded-xl bg-slate-950/60 border border-white/5">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Target Locality:</span>
                          <span className="text-white font-medium">{vl.society}, {vl.city}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Budget:</span>
                          <span className="text-emerald-400 font-bold">
                            PKR {(vl.budget_pkr / 10_000_000).toFixed(2)} Crore
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Visit Scheduled:</span>
                          <span className={`font-semibold ${vl.visit_booked === "yes" ? "text-emerald-400" : "text-slate-400"}`}>
                            {vl.visit_booked === "yes" ? "✅ Yes (Confirmed)" : "❌ No"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Purpose:</span>
                          <span className="text-cyan-300 capitalize">{vl.purpose || "Buy"}</span>
                        </div>
                      </div>

                      {/* Column 3: SLA Action Plan */}
                      <div className="space-y-1.5 p-3 rounded-xl bg-slate-950/60 border border-white/5">
                        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                          Required Closer Action & SLA
                        </span>
                        <div className="text-white font-semibold flex items-center gap-1.5 text-xs text-amber-300">
                          <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                          <span>{vl.action_plan || "Standard follow-up"}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-relaxed italic">
                          Recommended pitch: "{vl.recommended_pitch || 'Present prime sector inventory and verified prices.'}"
                        </p>
                      </div>
                    </div>

                    {/* Transcript Summary */}
                    {vl.transcript_summary && (
                      <div className="mb-4 p-3 rounded-xl bg-slate-950/40 border border-white/5">
                        <div className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-1 flex items-center gap-1.5">
                          <span>🎙️ Call Transcript Summary</span>
                        </div>
                        <p className="text-xs text-slate-300 font-light leading-relaxed">
                          "{vl.transcript_summary}"
                        </p>
                      </div>
                    )}

                    {/* Footer Actions */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-white/10">
                      <div className="flex items-center gap-2">
                        {vl.email_dispatched || isHot ? (
                          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span>
                              VIP Email Alert Dispatched to <strong className="text-white underline">{vl.assigned_employee_email || 'closer.vip@realestatehub.pk'}</strong>
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-xs text-slate-400">
                            <Clock className="w-3.5 h-3.5 text-slate-400" />
                            <span>Nurture workflow active (Email alert threshold: &ge; 70%)</span>
                          </div>
                        )}
                      </div>

                      {/* View Email Alert Preview Button */}
                      {(vl.email_dispatched || isHot || vl.email_body) && (
                        <button
                          onClick={() => setSelectedEmailAlert(vl)}
                          className="px-3.5 py-1.5 rounded-xl bg-red-500/15 hover:bg-red-500/25 border border-red-500/30 text-red-200 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm hover:scale-[1.02]"
                        >
                          <Mail className="w-3.5 h-3.5 text-red-400" />
                          <span>View VIP Alert Email</span>
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}

            {voiceLeads.length === 0 && (
              <div className="p-12 text-center glass-panel bg-slate-900/80 rounded-2xl border border-white/10 text-slate-400 text-xs">
                No voice calls recorded yet. Click <span className="text-amber-400 font-bold">"⚡ Test Hot Lead Webhook"</span> above to test lead scoring and view an automated alert!
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Add Property */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel p-6 max-w-lg w-full bg-slate-900 border border-white/20 rounded-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="font-heading font-bold text-lg text-white mb-4">Add Verified Property</h3>
            <form onSubmit={handleSaveAdd} className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Property Type</label>
                  <select
                    value={formProp.property_type}
                    onChange={(e) => setFormProp({ ...formProp, property_type: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  >
                    <option value="House">House</option>
                    <option value="Flat">Flat</option>
                    <option value="Upper Portion">Upper Portion</option>
                    <option value="Lower Portion">Lower Portion</option>
                    <option value="Farm House">Farm House</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Purpose</label>
                  <select
                    value={formProp.purpose}
                    onChange={(e) => setFormProp({ ...formProp, purpose: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  >
                    <option value="For Sale">For Sale</option>
                    <option value="For Rent">For Rent</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">City</label>
                  <select
                    value={formProp.city}
                    onChange={(e) => setFormProp({ ...formProp, city: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  >
                    <option value="Lahore">Lahore</option>
                    <option value="Islamabad">Islamabad</option>
                    <option value="Rawalpindi">Rawalpindi</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Locality</label>
                  <input
                    type="text"
                    required
                    value={formProp.locality}
                    onChange={(e) => setFormProp({ ...formProp, locality: e.target.value, location: `${e.target.value}, ${formProp.city}` })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Price (PKR)</label>
                  <input
                    type="number"
                    required
                    value={formProp.price}
                    onChange={(e) => setFormProp({ ...formProp, price: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Area Marla</label>
                  <input
                    type="number"
                    step="0.5"
                    required
                    value={formProp.area_marla}
                    onChange={(e) => setFormProp({ ...formProp, area_marla: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Bedrooms</label>
                  <input
                    type="number"
                    value={formProp.bedrooms}
                    onChange={(e) => setFormProp({ ...formProp, bedrooms: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Baths</label>
                  <input
                    type="number"
                    value={formProp.baths}
                    onChange={(e) => setFormProp({ ...formProp, baths: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Agent Name</label>
                <input
                  type="text"
                  value={formProp.agent}
                  onChange={(e) => setFormProp({ ...formProp, agent: e.target.value })}
                  className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Add Property
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Edit Property */}
      {editProperty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel p-6 max-w-lg w-full bg-slate-900 border border-white/20 rounded-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="font-heading font-bold text-lg text-white mb-4">Edit Property {editProperty.property_id}</h3>
            <form onSubmit={handleSaveEdit} className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Price (PKR)</label>
                  <input
                    type="number"
                    required
                    value={editProperty.price}
                    onChange={(e) => setEditProperty({ ...editProperty, price: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Area Marla</label>
                  <input
                    type="number"
                    step="0.5"
                    value={editProperty.area_marla}
                    onChange={(e) => setEditProperty({ ...editProperty, area_marla: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Locality</label>
                  <input
                    type="text"
                    value={editProperty.locality}
                    onChange={(e) => setEditProperty({ ...editProperty, locality: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Agent</label>
                  <input
                    type="text"
                    value={editProperty.agent}
                    onChange={(e) => setEditProperty({ ...editProperty, agent: e.target.value })}
                    className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setEditProperty(null)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Reschedule Appointment */}
      {rescheduleAppt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel p-6 max-w-md w-full bg-slate-900 border border-white/20 rounded-2xl">
            <h3 className="font-heading font-bold text-base text-white mb-2">Reschedule Visit</h3>
            <p className="text-xs text-slate-400 mb-4">
              Reschedule appointment for <span className="text-white font-semibold">{rescheduleAppt.client_name}</span>.
            </p>
            <form onSubmit={handleRescheduleSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">New Date</label>
                <input
                  type="text"
                  required
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">New Time</label>
                <input
                  type="text"
                  required
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Reason / Notes</label>
                <input
                  type="text"
                  value={reschedNotes}
                  onChange={(e) => setReschedNotes(e.target.value)}
                  className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
                <button type="button" onClick={() => setRescheduleAppt(null)} className="btn-secondary text-xs">
                  Cancel
                </button>
                <button type="submit" className="btn-primary text-xs">
                  Confirm Reschedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Cancel Appointment */}
      {cancelAppt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="glass-panel p-6 max-w-md w-full bg-slate-900 border border-white/20 rounded-2xl">
            <h3 className="font-heading font-bold text-base text-white mb-2">Cancel Appointment</h3>
            <p className="text-xs text-slate-400 mb-4">
              Are you sure you want to cancel the appointment for <span className="text-white font-semibold">{cancelAppt.client_name}</span>?
            </p>
            <form onSubmit={handleCancelSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Cancellation Reason</label>
                <input
                  type="text"
                  required
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  placeholder="e.g. Client requested cancellation"
                  className="w-full p-2 rounded-xl bg-slate-950 border border-white/10 text-xs text-white"
                />
              </div>
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/10">
                <button type="button" onClick={() => setCancelAppt(null)} className="btn-secondary text-xs">
                  Back
                </button>
                <button type="submit" className="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-400 text-white text-xs font-semibold">
                  Confirm Cancellation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: VIP Hot Lead Email Alert Preview (Task 4) */}
      {selectedEmailAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="glass-panel max-w-2xl w-full bg-[#0c101d] border border-red-500/30 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-4 bg-gradient-to-r from-red-950/80 to-slate-900 border-b border-red-500/30 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30 flex items-center justify-center">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-heading font-bold text-sm text-white flex items-center gap-2">
                    <span>🚨 Automated VIP Hot Lead Alert</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-500/30 text-red-200 font-mono">
                      {selectedEmailAlert.call_id}
                    </span>
                  </h3>
                  <div className="text-[11px] text-red-300/80">
                    Dispatched automatically upon voice call termination by Vapi telephony
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedEmailAlert(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Email Headers View */}
            <div className="p-4 bg-slate-950/80 border-b border-white/10 text-xs space-y-1.5 font-mono">
              <div className="flex">
                <span className="w-20 text-slate-500">FROM:</span>
                <span className="text-slate-300 font-semibold">automated-dispatch@realestatehub.pk</span>
              </div>
              <div className="flex">
                <span className="w-20 text-slate-500">TO:</span>
                <span className="text-amber-300 font-semibold">{selectedEmailAlert.assigned_employee_email || 'closer.vip@realestatehub.pk'}</span>
              </div>
              <div className="flex">
                <span className="w-20 text-slate-500">SUBJECT:</span>
                <span className="text-red-300 font-bold">{selectedEmailAlert.email_subject || `🚨 [VIP HOT LEAD] ${selectedEmailAlert.call_id} — ${selectedEmailAlert.conversion_score_pct}% Intent`}</span>
              </div>
              <div className="flex">
                <span className="w-20 text-slate-500">PRIORITY:</span>
                <span className="text-red-400 font-bold">HIGH (Immediate 15-Minute SLA Outreach)</span>
              </div>
            </div>

            {/* Email Body */}
            <div className="p-5 overflow-y-auto flex-1 text-xs text-slate-200 font-mono leading-relaxed bg-[#080b14] whitespace-pre-wrap select-text">
              {selectedEmailAlert.email_body || (
                `======================================================================
FROM: automated-dispatch@realestatehub.pk
TO: ${selectedEmailAlert.assigned_employee_email || 'closer.vip@realestatehub.pk'}
DATE: ${new Date(selectedEmailAlert.created_at || Date.now()).toUTCString()}
SUBJECT: 🚨 [VIP HOT LEAD] ${selectedEmailAlert.call_id} — ${selectedEmailAlert.conversion_score_pct}% Conversion Intent (SLA: < 15 minutes)
PRIORITY: HIGH (Immediate Action Required)
======================================================================

Dear Senior Closer / Sales Director,

A high-value prospect has just concluded an intake call with the Voice Agent.
The ML Lead Scoring Model has classified this lead as 🔥 HOT with ${selectedEmailAlert.conversion_score_pct}% conversion probability.

📋 LEAD DETAILS:
  • Call ID: ${selectedEmailAlert.call_id}
  • Caller Phone: ${selectedEmailAlert.caller_id}
  • Customer Persona: ${selectedEmailAlert.customer_persona || 'Luxury Villa Upgrader & HNI'}
  • Required SLA: < 15 minutes

🎙️ CALL TRANSCRIPT SUMMARY:
  "${selectedEmailAlert.transcript_summary}"

💡 RECOMMENDED SALES PLAYBOOK & PITCH:
  "${selectedEmailAlert.recommended_pitch || 'Highlight prime sector locations, corner park-facing plots, bespoke architecture, and privacy.'}"

🇵🇰 URDULISH REASONING:
  "Yeh lead 🔥 Hot hai (Conversion Probability: ${selectedEmailAlert.conversion_score_pct}%). Wajah: high buyer intent, site visit confirmed, DHA Phase 6 priority. Recommended SLA: < 15 minutes ke andar Senior Closer call kare."

Please initiate direct contact with the client immediately.
RealEstate-Hub CRM Automated Lead Dispatcher
----------------------------------------------------------------------`
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-slate-900 border-t border-white/10 flex items-center justify-between">
              <button
                onClick={() => {
                  const textToCopy = selectedEmailAlert.email_body || `Subject: ${selectedEmailAlert.email_subject}\n\nCall ID: ${selectedEmailAlert.call_id}\nCaller: ${selectedEmailAlert.caller_id}`;
                  navigator.clipboard.writeText(textToCopy);
                  setCopiedEmail(true);
                  setTimeout(() => setCopiedEmail(false), 2000);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
              >
                {copiedEmail ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedEmail ? "Copied to Clipboard!" : "Copy Email Text"}</span>
              </button>

              <button
                onClick={() => setSelectedEmailAlert(null)}
                className="px-4 py-1.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-semibold cursor-pointer"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

