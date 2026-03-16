import React, { useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Zap, Activity, Server, AlertTriangle } from 'lucide-react';

function Dashboard({ stats, onCaseLoad }) {
    const [selectedCase, setSelectedCase] = useState("case57");
    const [loading, setLoading] = useState(false);

    const handleLoad = async () => {
        setLoading(true);
        try {
            await onCaseLoad(selectedCase);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Prepare data for the chart
    const data = stats ? [
        { name: 'Generation', value: stats.total_gen_mw },
        { name: 'Load', value: stats.total_load_mw },
    ] : [];

    return (
        <div className="dashboard-panel">
            <h2><Zap size={20} color="#3b82f6" /> Power System Control</h2>

            <div className="control-group">
                <select value={selectedCase} onChange={(e) => setSelectedCase(e.target.value)}>
                    <option value="case57">IEEE Case 57</option>
                    <option value="case118">IEEE Case 118</option>
                    <option value="case14">IEEE Case 14</option>
                </select>
                <button onClick={handleLoad} disabled={loading}>
                    {loading ? "Loading..." : "Load Case"}
                </button>
            </div>

            <div className="stats-grid">
                <div className="stat-card">
                    <h3>Total Load</h3>
                    <p>{stats?.total_load_mw ? `${stats.total_load_mw.toFixed(1)} MW` : "-"}</p>
                </div>
                <div className="stat-card">
                    <h3>Total Gen</h3>
                    <p>{stats?.total_gen_mw ? `${stats.total_gen_mw.toFixed(1)} MW` : "-"}</p>
                </div>
                <div className="stat-card">
                    <h3>Buses</h3>
                    <p>{stats?.n_buses || "-"}</p>
                </div>
                <div className="stat-card warning">
                    <h3>Max Loading</h3>
                    <p>{stats?.max_line_loading_pct ? `${stats.max_line_loading_pct.toFixed(1)}%` : "-"}</p>
                </div>
                <div className={`stat-card ${stats?.voltage_violations > 0 ? 'danger' : ''}`}>
                    <h3>Voltage Viol.</h3>
                    <p>{stats?.voltage_violations ?? "-"}</p>
                </div>
                <div className={`stat-card ${stats?.current_violations > 0 ? 'danger' : ''}`}>
                    <h3>Current Viol.</h3>
                    <p>{stats?.current_violations ?? "-"}</p>
                </div>
            </div>

            {stats && (
                <div className="chart-container">
                    <h3>System Balance</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis type="category" dataKey="name" width={80} tick={{ fill: '#94a3b8' }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f1f5f9' }}
                                itemStyle={{ color: '#f1f5f9' }}
                            />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {data.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={index === 0 ? '#3b82f6' : '#8b5cf6'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    );
}

export default Dashboard;
