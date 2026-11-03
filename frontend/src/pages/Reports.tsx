import { useCallback, useMemo, useRef, useState } from 'react';
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Loader2,
  Minus,
  ScanText,
  Trash2,
  Upload,
} from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { apiError, reportsApi } from '../services/api';
import type { CompareResult, ReportAnalysis } from '../types';
import {
  Button,
  Card,
  EmptyState,
  ErrorBox,
  Heading,
  Notice,
  Spinner,
  Tag,
  fmtDateTime,
  fmtNumber,
  statusLabel,
  statusTone,
} from '../components/ui';

function StatusTag({ status }: { status: string }) {
  return <Tag tone={statusTone(status)}>{statusLabel(status)}</Tag>;
}

function RangeCell({
  low,
  high,
  unit,
}: {
  low: number | null;
  high: number | null;
  unit: string;
}) {
  if (low === null && high === null) return <span className="muted">Not published</span>;
  return (
    <span>
      {low ?? '—'} – {high ?? '—'} {unit}
    </span>
  );
}

function AnalysisResult({ report }: { report: ReportAnalysis }) {
  const flagged = report.parameters.filter(
    (p) => p.status === 'above_range' || p.status === 'below_range'
  );

  return (
    <Card className="result-card" style={{ marginTop: 16 }}>
      <div className="card-head">
        <div>
          <b>{report.filename}</b>
          <small className="small-note">Analysed {fmtDateTime(report.created_at)}</small>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <Tag tone="green">{report.counts.within_range} in range</Tag>
          <Tag tone="amber">{report.counts.flagged} flagged</Tag>
          <Tag tone="neutral">{report.counts.total} parameters</Tag>
        </div>
      </div>

      {report.extraction && (
        <p className="small-note" style={{ marginBottom: 10 }}>
          Extraction: <b>{report.extraction.method}</b>
          {report.extraction.pages ? ` · ${report.extraction.pages} page(s)` : ''}
          {report.extraction.ocr_used ? ' · OCR applied' : ' · digital text layer'}
        </p>
      )}

      {flagged.length > 0 && (
        <Notice tone="amber">
          <b>{flagged.length} value(s) fall outside the published reference range: </b>
          {flagged.map((p) => `${p.name} (${fmtNumber(p.value)} ${p.unit})`).join(', ')}. Discuss these
          with a clinician — a single out-of-range value is not a diagnosis.
        </Notice>
      )}

      <div className="table-wrap" style={{ marginTop: 12 }}>
        <table>
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Value</th>
              <th>Reference range</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {report.parameters.map((p, i) => (
              <tr key={`${p.name}-${i}`}>
                <td>
                  <b>{p.name}</b>
                  {p.source === 'ocr' && <span className="tag neutral" style={{ marginLeft: 6 }}>OCR</span>}
                  {p.source_page && <span className="small-note"> · page {p.source_page}</span>}
                  {p.confidence !== undefined && (
                    <span className="small-note"> · extraction confidence {Math.round(p.confidence * 100)}%</span>
                  )}
                </td>
                <td>
                  <b>{fmtNumber(p.value)}</b> <span className="muted">{p.unit}</span>
                </td>
                <td>
                  <RangeCell low={p.ref_low} high={p.ref_high} unit={p.unit} />
                </td>
                <td>
                  <StatusTag status={p.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="small-note" style={{ marginTop: 12 }}>
        <b>Summary: </b>
        {report.summary}
      </p>
      <p className="demo-caption">{report.disclaimer}</p>
    </Card>
  );
}

function ComparePanel({ result }: { result: CompareResult }) {
  const directionIcon = (d: string) =>
    d === 'up' ? <ArrowUpRight size={12} /> : d === 'down' ? <ArrowDownRight size={12} /> : <Minus size={12} />;

  return (
    <Card className="result-card" style={{ marginTop: 16 }}>
      <div className="card-head">
        <div>
          <b>Comparison</b>
          <small className="small-note">
            {result.older.filename} ({fmtDateTime(result.older.created_at)}) → {result.newer.filename} (
            {fmtDateTime(result.newer.created_at)})
          </small>
        </div>
        <Tag tone="blue">{result.compared} compared</Tag>
      </div>

      <div className="compare-split">
        <div>
          <small className="small-note">Improved</small>
          {result.improved.length === 0 ? (
            <p className="small-note">None detected.</p>
          ) : (
            <div className="lang-chips">
              {result.improved.map((n) => (
                <span className="chip-static green" key={n}>
                  <CheckCircle2 size={11} /> {n}
                </span>
              ))}
            </div>
          )}
        </div>
        <div>
          <small className="small-note">Worsened</small>
          {result.worsened.length === 0 ? (
            <p className="small-note">None detected.</p>
          ) : (
            <div className="lang-chips">
              {result.worsened.map((n) => (
                <span className="chip-static amber" key={n}>
                  {n}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Previous</th>
              <th>Current</th>
              <th>Change</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {result.rows.map((row) => (
              <tr key={row.name}>
                <td>
                  <b>{row.name}</b>
                  {row.direction === 'new' && (
                    <span className="tag blue" style={{ marginLeft: 6 }}>
                      NEW
                    </span>
                  )}
                </td>
                <td>{row.previous === null ? '—' : `${fmtNumber(row.previous)} ${row.unit}`}</td>
                <td>
                  <b>{fmtNumber(row.current)}</b> <span className="muted">{row.unit}</span>
                </td>
                <td style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  {directionIcon(row.direction)}
                  {row.change === null ? '—' : `${row.change > 0 ? '+' : ''}${fmtNumber(row.change, 2)}`}
                  {row.percent_change !== null && (
                    <span className="muted">({row.percent_change > 0 ? '+' : ''}{fmtNumber(row.percent_change, 1)}%)</span>
                  )}
                </td>
                <td>
                  <StatusTag status={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.new_parameters > 0 && (
        <p className="small-note" style={{ marginTop: 10 }}>
          {result.new_parameters} parameter(s) appear only in the newer report and cannot be compared.
        </p>
      )}
      <p className="small-note" style={{ marginTop: 10 }}>
        <b>Summary: </b>
        {result.summary}
      </p>
      <p className="demo-caption">{result.disclaimer}</p>
    </Card>
  );
}

export default function Reports() {
  const ocr = useAsync(() => reportsApi.ocrStatus().then((r) => r.data), []);
  const list = useAsync(() => reportsApi.list().then((r) => r.data), []);

  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [analysis, setAnalysis] = useState<ReportAnalysis | null>(null);

  const [selected, setSelected] = useState<number[]>([]);
  const [comparing, setComparing] = useState(false);
  const [compare, setCompare] = useState<CompareResult | null>(null);

  const fileInput = useRef<HTMLInputElement | null>(null);

  const upload = useCallback(
    async (file: File) => {
      setError('');
      setCompare(null);
      setUploading(true);
      try {
        const { data } = await reportsApi.analyze(file);
        setAnalysis(data);
        await list.reload();
      } catch (err) {
        setError(apiError(err, 'Could not analyse that file.'));
      } finally {
        setUploading(false);
      }
    },
    [list]
  );

  const onFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) void upload(file);
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length >= 2 ? [prev[1], id] : [...prev, id]
    );
  };

  const runCompare = async () => {
    if (selected.length !== 2) return;
    setError('');
    setComparing(true);
    try {
      const { data } = await reportsApi.compare(selected);
      setCompare(data);
      setAnalysis(null);
    } catch (err) {
      setError(apiError(err, 'Could not compare those reports.'));
    } finally {
      setComparing(false);
    }
  };

  const removeReport = async (id: number) => {
    setError('');
    try {
      await reportsApi.remove(id);
      setSelected((prev) => prev.filter((x) => x !== id));
      if (analysis?.id === id) setAnalysis(null);
      await list.reload();
    } catch (err) {
      setError(apiError(err, 'Could not delete that report.'));
    }
  };

  const reports = list.data ?? [];
  const ocrAvailable = ocr.data?.available ?? false;

  const selectedNames = useMemo(
    () => reports.filter((r) => selected.includes(r.id)).map((r) => r.filename),
    [reports, selected]
  );

  return (
    <>
      <Heading
        eyebrow="REPORT ANALYZER"
        title="Turn a lab report into readable numbers"
        desc="Upload a PDF or a photo. MediSense extracts each parameter, compares it with its reference range and flags what is out of bounds."
      />

      {!ocr.loading && !ocrAvailable && (
        <Notice tone="amber">
          <b>OCR is not available on this server.</b> Digital (text-based) PDFs work fully. Scanned
          images and image-only PDFs need the OCR extra installed — MediSense will tell you when it
          cannot read a file rather than guessing values.
        </Notice>
      )}

      <div className="report-grid" style={{ marginTop: 16 }}>
        <Card className="upload-card">
          <div
            className={`dropzone ${dragging ? 'dragging' : ''} ${uploading ? 'busy' : ''}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              onFiles(e.dataTransfer.files);
            }}
            onClick={() => fileInput.current?.click()}
            role="button"
            tabIndex={0}
          >
            <input
              ref={fileInput}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff"
              hidden
              onChange={(e) => onFiles(e.target.files)}
            />
            {uploading ? (
              <>
                <div className="upload-symbol">
                  <Loader2 size={22} className="spin" />
                </div>
                <b>Extracting parameters…</b>
                <p className="muted">Reading the document and matching reference ranges.</p>
              </>
            ) : (
              <>
                <div className="upload-symbol">
                  <Upload size={22} />
                </div>
                <b>Drop a report here</b>
                <p className="muted">PDF, PNG, JPG or TIFF · up to the server upload limit</p>
                <span className="btn primary" style={{ marginTop: 12 }}>
                  <FileText size={14} /> Choose a file
                </span>
              </>
            )}
          </div>

          {error && <ErrorBox message={error} />}

          <div className="upload-meta">
            <div>
              <ImageIcon size={14} />
              <span>Images {ocrAvailable ? 'supported' : 'need OCR'}</span>
            </div>
            <div>
              <ScanText size={14} />
              <span>Engine: {ocr.data?.engine ?? 'text layer'}</span>
            </div>
          </div>

          <p className="small-note" style={{ marginTop: 12 }}>
            Reference ranges come from the report itself where published. MediSense never invents a
            range — parameters without one are labelled <b>No reference</b>.
          </p>
        </Card>

        <Card>
          <div className="card-head">
            <div>
              <b>Your reports</b>
              <small className="small-note">Select exactly two to compare</small>
            </div>
            <Tag tone="neutral">{reports.length}</Tag>
          </div>

          {list.loading && <Spinner label="Loading reports…" />}
          {!list.loading && reports.length === 0 && (
            <EmptyState
              icon={<FileText size={18} />}
              title="No reports stored"
              desc="Your first upload will appear here."
            />
          )}

          <div className="report-list">
            {reports.map((r) => (
              <div className={`list-row selectable ${selected.includes(r.id) ? 'picked' : ''}`} key={r.id}>
                <input
                  type="checkbox"
                  checked={selected.includes(r.id)}
                  onChange={() => toggleSelect(r.id)}
                  aria-label={`Compare ${r.filename}`}
                />
                <div className="file-icon">
                  <FileText size={15} />
                </div>
                <div>
                  <b>{r.filename}</b>
                  <small>
                    {fmtDateTime(r.created_at)} · {r.total_parameters} params · {r.flagged} flagged
                  </small>
                </div>
                <button
                  className="icon-btn"
                  onClick={() => void removeReport(r.id)}
                  title="Delete report"
                  aria-label="Delete report"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>

          <Button full onClick={() => void runCompare()} disabled={selected.length !== 2 || comparing}>
            {comparing ? <Loader2 size={14} className="spin" /> : <ArrowRight size={14} />}
            {comparing ? 'Comparing…' : `Compare (${selected.length}/2)`}
          </Button>
          {selected.length > 0 && (
            <p className="small-note" style={{ marginTop: 8 }}>
              Selected: {selectedNames.join(' vs ') || '—'}
            </p>
          )}
        </Card>
      </div>

      {analysis && <AnalysisResult report={analysis} />}
      {compare && <ComparePanel result={compare} />}
    </>
  );
}
