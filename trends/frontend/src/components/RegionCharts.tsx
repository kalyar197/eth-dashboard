// src/components/RegionCharts.tsx
/**
 * Region Charts Tab - View trends by region across all keywords
 * Minimalist dropdown + line chart
 */

import { useState, useEffect } from 'react';
import { getRegions, getTrendDataForRegion, type Region } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const KEYWORD_COLORS = [
  '#00D9FF', '#FF6B35', '#00FF87', '#FFD700', '#FF1744',
  '#9D4EDD', '#06FFA5', '#FF006E', '#00B4D8', '#FF9F1C'
];

export function RegionCharts() {
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRegions();
  }, []);

  useEffect(() => {
    if (selectedRegion) {
      fetchChartData();
    }
  }, [selectedRegion]);

  const fetchRegions = async () => {
    try {
      const data = await getRegions();
      setRegions(data);
      if (data.length > 0 && !selectedRegion) {
        setSelectedRegion(data[0].code);
      }
    } catch (err) {
      console.error('Failed to fetch regions:', err);
    }
  };

  const fetchChartData = async () => {
    if (!selectedRegion) return;

    setLoading(true);
    try {
      const data = await getTrendDataForRegion(selectedRegion);

      // Transform data for Recharts
      // data format: {keyword: [[timestamp, value], ...], ...}
      const allTimestamps = new Set<number>();
      Object.values(data).forEach((keywordData: any) => {
        keywordData.forEach(([timestamp]: [number, number]) => {
          allTimestamps.add(timestamp);
        });
      });

      const sortedTimestamps = Array.from(allTimestamps).sort((a, b) => a - b);

      const transformed = sortedTimestamps.map(timestamp => {
        const point: any = {
          date: new Date(timestamp).toLocaleDateString(),
          timestamp
        };

        Object.entries(data).forEach(([keyword, keywordData]: [string, any]) => {
          const dataPoint = keywordData.find(([ts]: [number, number]) => ts === timestamp);
          point[keyword] = dataPoint ? dataPoint[1] : null;
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

  const getRegionLabel = (code: string) => {
    const region = regions.find(r => r.code === code);
    return region ? `${region.label} (${region.code})` : code;
  };

  return (
    <div className="p-4 space-y-4">
      {/* Region Selector */}
      <div className="flex gap-2 items-center">
        <label className="text-sm">Region:</label>
        <select
          className="input"
          value={selectedRegion}
          onChange={(e) => setSelectedRegion(e.target.value)}
        >
          {regions.map((region) => (
            <option key={region.code} value={region.code}>
              {region.label} ({region.code})
            </option>
          ))}
        </select>
      </div>

      {/* Chart */}
      {loading ? (
        <div className="text-center text-muted py-8">Loading...</div>
      ) : chartData.length === 0 ? (
        <div className="text-center text-muted py-8">
          No data available for {getRegionLabel(selectedRegion)}. Add keywords in Management tab.
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
                .map((keyword, idx) => (
                  <Line
                    key={keyword}
                    type="monotone"
                    dataKey={keyword}
                    stroke={KEYWORD_COLORS[idx % KEYWORD_COLORS.length]}
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
