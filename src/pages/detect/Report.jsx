import { Link, useLocation } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/16/solid';
import DetectionReport from '../../components/DetectionReport';

const getStoredReport = () => {
  try {
    const stored = sessionStorage.getItem('tomato-planet-last-report');
    return stored ? JSON.parse(stored) : null;
  } catch {
    return null;
  }
};

const DetectReport = () => {
  const location = useLocation();
  const report = location.state || getStoredReport();

  if (!report?.result) {
    return (
      <div className="px-[20px] lg:px-[120px] py-[80px] min-h-[60vh] bg-white">
        <div className="max-w-[720px] rounded-[18px] border border-black/10 p-8 shadow-sm">
          <h1 className="text-[34px] font-semibold">No report available</h1>
          <p className="text-tertiary text-[18px] pt-3 leading-relaxed">
            Run a new analysis first, then use the view results button to open the report.
          </p>
          <Link to="/detect" className="inline-block py-[14px] text-[18px] text-white px-[32px] rounded-[18px] bg-primary mt-6">
            Analyze an image
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="px-[20px] lg:px-[80px] xl:px-[120px] py-[32px] lg:py-[48px] overflow-x-hidden bg-[#FAFAF8] min-h-screen">
      <div className="pb-7 print:hidden">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5">
          <div>
            <Link to="/detect" className="inline-flex items-center gap-2 text-primary font-semibold hover:text-secondary">
              <ArrowLeftIcon className="h-4 w-4" />
              Back to analysis
            </Link>
            <h1 className="text-[34px] lg:text-[46px] font-semibold pt-3">Assessment Report</h1>
            <p className="text-tertiary text-[17px] pt-1">Review the detection result and recommended treatment plan.</p>
          </div>
          <Link to="/detect" className="inline-flex justify-center py-[13px] text-[17px] text-white px-[24px] rounded-[14px] bg-primary shadow-sm hover:opacity-95 transition-opacity">
            New analysis
          </Link>
        </div>
      </div>
      <DetectionReport
        image={report.image}
        result={report.result}
        treatment={report.treatment}
        reportDate={report.reportDate}
      />
    </div>
  );
};

export default DetectReport;
