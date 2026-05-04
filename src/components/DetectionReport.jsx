import { useRef } from 'react';
import PropTypes from 'prop-types';
import ReactToPrint from 'react-to-print';

const formatPercent = (value) => {
  if (typeof value !== 'number') return '0.00%';
  if (value >= 0.9995) return '>99.9%';
  return `${(value * 100).toFixed(2)}%`;
};

const treatmentLabels = {
  biological: 'Biological care',
  chemical: 'Chemical care',
  prevention: 'Prevention',
};

const DetectionReport = ({ image, result, treatment, reportDate }) => {
  const componentRef = useRef();
  const summary = result?.summary;
  const primaryDisease = summary?.primary_disease;
  const secondaryDiseases = summary?.secondary_diseases || [];
  const isHealthyResult = primaryDisease?.class === 'Healthy Tomato Leaf';
  const isNonTomatoLeafResult = primaryDisease?.class === 'Non-Tomato Leaf';
  const isUncertainResult = Boolean(summary?.is_uncertain && !primaryDisease);
  const uncertaintyReason = summary?.uncertainty_reason || summary?.visual_consistency?.reason;
  const confidenceLevel = primaryDisease?.best_confidence || primaryDisease?.average_confidence || 0;
  const checkedRegions = summary?.unique_region_count || summary?.region_count || 0;
  const processingTimeSeconds = typeof summary?.processing_time_ms === 'number'
    ? (summary.processing_time_ms / 1000).toFixed(1)
    : null;

  return (
    <div ref={componentRef} className="print-report bg-white rounded-[20px] border border-black/5 shadow-sm p-4 md:p-6 lg:p-8">
      <div className="hidden print:block print-report-header">
        <p className="print-report-brand">Tomato Planet</p>
        <h1>Tomato Disease Assessment</h1>
        <p>Generated: {reportDate}</p>
      </div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-6 border-b border-black/5 print:hidden">
        <div>
          <p className="text-[14px] uppercase tracking-[0.08em] text-primary font-semibold">Tomato Planet</p>
          <p className="text-tertiary text-[16px] pt-1">Generated: {reportDate}</p>
        </div>
        <div className="flex flex-wrap gap-2 text-[14px] text-tertiary">
          {checkedRegions > 0 && (
            <span className="rounded-full bg-black/[0.04] px-4 py-2">Regions checked: {checkedRegions}</span>
          )}
          {processingTimeSeconds && (
            <span className="rounded-full bg-black/[0.04] px-4 py-2">Processed in {processingTimeSeconds}s</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(320px,0.88fr)_minmax(0,1.12fr)] gap-7 lg:gap-9 items-start pt-6 print-report-body">
        <div className="md:sticky md:top-24 print:static print-image-wrap">
          <div className="rounded-[18px] bg-[#F4F6F2] border border-black/5 p-3">
            {image ? (
              <img src={image} alt="Analyzed upload" className="w-full max-h-[620px] rounded-[12px] object-cover print-image" />
            ) : (
              <div className="min-h-[360px] rounded-[12px] border border-dashed border-black/10 bg-white flex items-center justify-center text-tertiary">
                No image preview available
              </div>
            )}
            <div className="pt-4 px-1 print:hidden">
              <p className="font-semibold text-[18px]">Uploaded image</p>
              <p className="text-tertiary text-[15px] pt-1">Use this preview to confirm the report matches the intended leaf photo.</p>
            </div>
          </div>
        </div>

        <div className="print-card">
          {isUncertainResult ? (
            <div className="rounded-[18px] bg-[#FFF8E6] border border-[#F2DCA2] p-5 lg:p-6">
              <p className="text-[14px] uppercase tracking-[0.08em] text-quaternary font-semibold">Detection result</p>
              <p className="font-bold text-[28px] text-quaternary pt-2 print-section-title">Uncertain</p>
              <p className="text-tertiary text-[18px] pt-3 leading-relaxed">
                The backend could not confidently classify this image. Try a sharper close-up where the affected leaf fills most of the frame.
              </p>
              {uncertaintyReason && (
                <p className="text-tertiary text-[14px] pt-3 leading-relaxed">
                  Backend reason: {uncertaintyReason.replaceAll('_', ' ')}
                </p>
              )}
            </div>
          ) : (
            <div className="rounded-[18px] bg-[#FFF8F8] border border-primary/10 p-5 lg:p-6">
              <p className="text-[14px] uppercase tracking-[0.08em] text-primary font-semibold">Primary result</p>
              <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 pt-2">
                <p className="font-bold text-[32px] lg:text-[38px] leading-tight print-section-title text-primary">
                  {primaryDisease?.class}
                </p>
                <span className="w-fit rounded-full bg-primary text-white px-4 py-2 text-[15px]">
                  Model score: {formatPercent(confidenceLevel)}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-5 print-metrics">
                <div className="rounded-[12px] bg-white border border-black/5 p-4 print-metric">
                  <p className="text-[14px] text-tertiary">Detection score</p>
                  <p className="font-semibold text-[22px] pt-1">{primaryDisease?.score?.toFixed(3)}</p>
                </div>
                <div className="rounded-[12px] bg-white border border-black/5 p-4 print-metric">
                  <p className="text-[14px] text-tertiary">Regions found</p>
                  <p className="font-semibold text-[22px] pt-1">{primaryDisease?.region_count}</p>
                </div>
                <div className="rounded-[12px] bg-white border border-black/5 p-4 print-metric">
                  <p className="text-[14px] text-tertiary">Regions checked</p>
                  <p className="font-semibold text-[22px] pt-1">{checkedRegions}</p>
                </div>
              </div>
              <p className="pt-3 text-[14px] leading-relaxed text-tertiary print:hidden">
                Detection score combines the strongest model score, average regional score, and how many checked regions support the result.
              </p>
            </div>
          )}

          {secondaryDiseases.length > 0 && (
            <div className="pt-6 print-section">
              <p className="text-[14px] uppercase tracking-[0.08em] text-tertiary font-semibold">Additional signal</p>
              <p className="pt-2 text-[15px] leading-relaxed text-tertiary print:hidden">
                Additional signals are other classes with notable evidence, but less overall support than the primary result.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-3">
                {secondaryDiseases.map((disease) => (
                  <div key={disease.class} className="rounded-[12px] border border-black/5 bg-white p-4 print-metric">
                    <p className="font-semibold text-[18px]">{disease.class}</p>
                    <p className="text-tertiary pt-1">Model score: {formatPercent(disease.best_confidence)} | Regions: {disease.region_count}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {treatment && (
            <div className="pt-7 print-section">
              <div className="border-t border-black/5 pt-6">
                <p className="text-[14px] uppercase tracking-[0.08em] text-secondary font-semibold">Treatment plan</p>
                <p className="font-semibold text-[28px] pt-2 print-section-title">{treatment.name}</p>
                <p className="text-tertiary text-[18px] pt-2 leading-relaxed">{treatment.description}</p>
              </div>
              <div className="pt-5 space-y-4">
                {['biological', 'chemical', 'prevention'].map((section) => (
                  treatment[section]?.length > 0 && (
                    <div key={section} className="rounded-[14px] bg-[#F8FAF7] border border-black/5 p-5 print-treatment-block">
                      <h3 className="font-semibold text-[19px]">{treatmentLabels[section]}</h3>
                      <ul className="pt-3 text-tertiary text-[17px] space-y-2">
                        {treatment[section].map((item) => (
                          <li key={item} className="flex gap-3 leading-relaxed">
                            <span className="mt-[10px] h-2 w-2 shrink-0 rounded-full bg-secondary" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {!treatment && isHealthyResult && (
            <div className="pt-7 print-section">
              <div className="border-t border-black/5 pt-6">
                <p className="text-[14px] uppercase tracking-[0.08em] text-secondary font-semibold">Health status</p>
                <p className="font-semibold text-[28px] pt-2 print-section-title">No disease detected</p>
                <p className="text-tertiary text-[18px] pt-2 leading-relaxed">
                  The uploaded tomato leaf appears healthy based on the current analysis. Keep monitoring the plant and use clear close-up photos if symptoms appear later.
                </p>
              </div>
            </div>
          )}

          {!treatment && isNonTomatoLeafResult && (
            <div className="pt-7 print-section">
              <div className="border-t border-black/5 pt-6">
                <p className="text-[14px] uppercase tracking-[0.08em] text-quaternary font-semibold">Leaf category</p>
                <p className="font-semibold text-[28px] pt-2 print-section-title">Non-tomato leaf detected</p>
                <p className="text-tertiary text-[18px] pt-2 leading-relaxed">
                  The upload appears to be a leaf, but the model classified it as outside the supported tomato leaf categories. No tomato treatment plan is shown.
                </p>
              </div>
            </div>
          )}

          <ReactToPrint
            trigger={() => <button className="print-button w-full sm:w-auto py-[14px] text-[18px] text-white px-[34px] rounded-[14px] bg-primary mt-7 shadow-sm hover:opacity-95 transition-opacity">Print report</button>}
            content={() => componentRef.current}
          />
        </div>
      </div>
    </div>
  );
};

export default DetectionReport;

DetectionReport.propTypes = {
  image: PropTypes.string,
  reportDate: PropTypes.string,
  result: PropTypes.shape({
    summary: PropTypes.shape({
      is_uncertain: PropTypes.bool,
      unique_region_count: PropTypes.number,
      region_count: PropTypes.number,
      primary_disease: PropTypes.shape({
        class: PropTypes.string,
        score: PropTypes.number,
        region_count: PropTypes.number,
        best_confidence: PropTypes.number,
        average_confidence: PropTypes.number,
      }),
      secondary_diseases: PropTypes.arrayOf(PropTypes.shape({
        class: PropTypes.string,
        region_count: PropTypes.number,
        best_confidence: PropTypes.number,
      })),
      processing_time_ms: PropTypes.number,
    }),
  }).isRequired,
  treatment: PropTypes.shape({
    name: PropTypes.string,
    description: PropTypes.string,
    biological: PropTypes.arrayOf(PropTypes.string),
    chemical: PropTypes.arrayOf(PropTypes.string),
    prevention: PropTypes.arrayOf(PropTypes.string),
  }),
};

DetectionReport.defaultProps = {
  image: '',
  reportDate: '',
  treatment: null,
};
