// src/components/WordCharts.tsx
/**
 * Word Charts Tab - View trends by keyword across all regions
 * Minimalist dropdown + line chart
 */

import { useState, useEffect } from 'react';
import { getKeywords, getTrendDataForKeyword, getRegions, type Keyword, type Region } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const REGION_COLORS = [
  '#00D9FF', '#FF6B35', '#00FF87', '#FFD700', '#FF1744',
  '#9D4EDD', '#06FFA5', '#FF006E', '#00B4D8', '#FF9F1C',
  '#06FF7A', '#FF006B'
];

export function WordCharts() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedKeyword, setSelectedKeyword] = useState<string>('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchKeywords();
    fetchRegions();
  }, []);

  useEffect(() => {
    if (selectedKeyword) {
      fetchChartData();
    }
  }, [selectedKeyword]);

  const fetchKeywords = async () => {
    try {
      const data = await getKeywords();
      setKeywords(data.filter(k => k.status === 'completed' || k.status === 'partial'));
      if (data.length > 0 && !selectedKeyword) {
        setSelectedKeyword(data[0].keyword);
      }
    } catch (err) {
      console.error('Failed to fetch keywords:', err);
    }
  };

  const fetchRegions = async () => {
    try {
      const data = await getRegions();
      setRegions(data);
    } catch (err) {
      console.error('Failed to fetch regions:', err);
    }
  };

  const fetchChartData = async () => {
    if (!selectedKeyword) return;

    setLoading(true);
    try {
      const data = await getTrendDataForKeyword(selectedKeyword);

      // Transform data for Recharts
      // data format: {region: [[timestamp, value], ...], ...}
      const allTimestamps = new Set<number>();
      Object.values(data).forEach((regionData: any) => {
        regionData.forEach(([timestamp]: [number, number]) => {
          allTimestamps.add(timestamp);
        });
      });

      const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);

      const transformed = sortedTimestamps.map(timestamp => {
        const point: any = {
          date: new Date(timestamp).toLocaleDateString(),
          timestamp
        };

        Object.entries(data).forEach(([region, regionData]: [string, any]) => {
          const dataPoint = regionData.find(([ts]: [number, number]) => ts === timestamp);
          point[region] = dataPoint ? dataPoint[1] : null;
        });

        return point;
      });

      setChartData(transformed);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      {/* Keyword Selector */}
      <div className="flex gap-2 items-center">
        <label className="text-sm">Keyword:</label>
        <select
          className="input"
          value={selectedKeyword}
          onChange={(e) => setSelectedKeyword(e.target.value)}
        >
          {keywords.map((kw) => (
            <option key={kw.id} value={kw.keyword}>
              {kw.keyword}
            </option>
          ))}
        </select>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="text-center text-muted py-8">Loading...</div>
      ) : chartData.length === 0 ? (
        <div className="text-center text-muted py-8">
          No data available. Add keywords in Management tab.
        </div>
      ) : (
        <div className="bg-secondary p-4 rounded">
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3a3a3a" />
              <XAxis
                dataKey="date"
                stroke="#ffffff"
                style={{ fontSize: '12px', fontFamily: 'monospace' }}
              />
              <YAxis
                domain={[0, 100]}
                stroke="#ffffff"
                style={{ fontSize: '12px', fontFamily: 'monospace' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#2a2a2a',
                  border: '1px solid #3a3a3a',
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
              />
              <Legend
                wrapperStyle={{
                  fontFamily: 'monospace',
                  fontSize: '11px'
                }}
              />
              {Object.keys(chartData[0] || {})
                .filter(key => key !== 'date' && key !== 'timestamp')
                .map((region, idx) => (
                  <Line
                    key={region}
                    type="monotone"
                    dataKey={region}
                    stroke={REGION_COLORS[idx % REGION_COLORS.length]}
                    dot={false}
                    strokeWidth={2}
                    connectNulls
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
