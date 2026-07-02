// Central Chart.js registration so every analytics block shares one setup.
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Tooltip,
  Legend,
)

// Fallback palette for categorical charts (doughnut) that don't carry per-item colors.
export const PALETTE = [
  '#1552b3',
  '#b45309',
  '#15803d',
  '#b91c1c',
  '#7c3aed',
  '#0891b2',
  '#c2410c',
  '#4d7c0f',
]
