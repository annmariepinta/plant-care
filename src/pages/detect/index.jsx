import { useRef, useState } from 'react';
import axios from 'axios';
import { PhotoIcon } from '@heroicons/react/16/solid';
import { useNavigate } from 'react-router-dom';
import { useAppToast } from '../../lib/UseAppToast';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';
const ANALYSIS_MAX_DIMENSION = 1024;
const ANALYSIS_IMAGE_QUALITY = 0.9;
const TREATABLE_DISEASES = new Set(['Early Blight', 'Late Blight', 'Leaf Mold']);

const treatmentKey = (name) => name?.trim().toLowerCase().replaceAll('_', '-').replaceAll(' ', '-');

const resizeImageForAnalysis = (file) => new Promise((resolve) => {
    if (!file.type.startsWith('image/') || file.type === 'image/gif') {
        resolve(file);
        return;
    }

    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
        URL.revokeObjectURL(objectUrl);

        const largestSide = Math.max(img.width, img.height);
        if (largestSide <= ANALYSIS_MAX_DIMENSION) {
            resolve(file);
            return;
        }

        const scale = ANALYSIS_MAX_DIMENSION / largestSide;
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(img.width * scale);
        canvas.height = Math.round(img.height * scale);

        const context = canvas.getContext('2d');
        if (!context) {
            resolve(file);
            return;
        }

        context.drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
            (blob) => resolve(blob || file),
            'image/jpeg',
            ANALYSIS_IMAGE_QUALITY,
        );
    };

    img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        resolve(file);
    };

    img.src = objectUrl;
});

const Detect = () => {
    const navigate = useNavigate();
    const toast = useAppToast();
    const fileInputRef = useRef(null);
    const [selectedImage, setSelectedImage] = useState(null);
    const [image, setImage] = useState(null);
    const [reportPayload, setReportPayload] = useState(null);
    const [loader, setLoader] = useState(false);

    const handleImageUpload = async () => {
        if (!selectedImage || !image) {
            toast({
                status: 'error',
                description: 'Please select an image',
            });
            return;
        }

        setLoader(true);
        setReportPayload(null);

        try {
            const uploadImage = await resizeImageForAnalysis(selectedImage);
            const formData = new FormData();
            formData.append('file', uploadImage, selectedImage.name || 'tomato-upload.jpg');

            const response = await axios.post(`${API_BASE_URL}/predict-regions?profile=fast`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            const data = response.data;
            if (data?.summary?.is_supported_leaf_image === false) {
                toast({
                    status: 'error',
                    description: 'This is not a leaf image. Please upload a clear leaf photo.',
                });
                return;
            }

            let treatmentData = null;

            const primaryDisease = data?.summary?.primary_disease?.class;
            const hasPrimaryDisease = Boolean(primaryDisease);
            const hasConfidentPrimaryDisease = hasPrimaryDisease && TREATABLE_DISEASES.has(primaryDisease);
            if (hasConfidentPrimaryDisease) {
                try {
                    const treatmentResponse = await axios.get(`${API_BASE_URL}/treatment/${treatmentKey(primaryDisease)}`);
                    treatmentData = treatmentResponse.data;
                } catch {
                    treatmentData = null;
                }
            }

            const nextReportPayload = {
                image,
                result: data,
                treatment: treatmentData,
                reportDate: new Date().toLocaleString(),
            };

            setReportPayload(nextReportPayload);

            try {
                sessionStorage.setItem('tomato-planet-last-report', JSON.stringify(nextReportPayload));
            } catch {
                sessionStorage.removeItem('tomato-planet-last-report');
            }

            toast({
                status: data?.summary?.is_uncertain && !hasPrimaryDisease ? 'warning' : 'success',
                description: data?.summary?.is_uncertain && !hasPrimaryDisease
                    ? 'Analysis complete, but the model is uncertain. Try a closer leaf photo if needed.'
                    : 'Analysis successful',
            });

            navigate('/detect/report', { state: nextReportPayload });
        } catch (error) {
            toast({
                status: 'error',
                description: error?.response?.data?.detail || 'Could not analyze image. Make sure the backend is running.',
            });
        } finally {
            setLoader(false);
        }
    };

    const handleImageChange = (event) => {
        const file = event.target.files?.[0];
        setSelectedImage(file || null);
        setReportPayload(null);

        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImage(reader.result);
            };
            reader.readAsDataURL(file);
        } else {
            setImage(null);
        }
    };

    const handleViewReport = () => {
        if (reportPayload) {
            navigate('/detect/report', { state: reportPayload });
        }
    };

    const openFilePicker = () => {
        fileInputRef.current?.click();
    };

    const handleUploadAreaKeyDown = (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openFilePicker();
        }
    };

    return (
        <div className="px-[20px] lg:px-[80px] xl:px-[120px] py-[32px] lg:py-[56px] overflow-x-hidden bg-[#FAFAF8] min-h-screen">
            <div className="max-w-[1180px] mx-auto">
                <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,0.9fr)_minmax(360px,1.1fr)] gap-8 lg:gap-12 items-start">
                    <div className="pt-2 lg:pt-8">
                        <p className="text-[14px] uppercase tracking-[0.08em] text-primary font-semibold">Tomato disease analyzer</p>
                        <h1 className="text-[38px] lg:text-[54px] leading-tight font-semibold pt-3">
                            Upload a tomato leaf photo
                        </h1>
                        <p className="text-[17px] lg:text-[19px] text-tertiary pt-4 leading-relaxed max-w-[560px]">
                            Get a focused disease assessment and treatment plan for Early Blight, Late Blight, and Leaf Mold.
                        </p>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-8 max-w-[720px]">
                            {['Close-up leaf', 'Natural light', 'Plain background'].map((tip) => (
                                <div key={tip} className="rounded-[14px] bg-white border border-black/5 px-4 py-3 shadow-sm">
                                    <p className="font-semibold text-[15px]">{tip}</p>
                                </div>
                            ))}
                        </div>

                        <div className="mt-8 rounded-[18px] border border-black/5 bg-white p-5 lg:p-6 shadow-sm">
                            <h2 className="text-[20px] font-semibold">Supported images</h2>
                            <p className="text-[16px] text-tertiary pt-2 leading-relaxed">
                                Use a clear tomato leaf photo where the leaf is the main subject. Logos, documents, vehicles, people, diagrams, and distant background vegetation are blocked.
                            </p>
                        </div>
                    </div>

                    <div className="rounded-[20px] bg-white border border-black/5 shadow-sm p-4 lg:p-6">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleImageChange}
                            className="sr-only"
                        />
                        <div
                            role="button"
                            tabIndex={0}
                            onClick={openFilePicker}
                            onKeyDown={handleUploadAreaKeyDown}
                            className="cursor-pointer rounded-[16px] border border-dashed border-primary/50 bg-[#FAFAF8] p-4 text-center transition-colors hover:bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 lg:p-5"
                            aria-label={image ? 'Change uploaded image' : 'Upload an image'}
                        >
                            {image ? (
                                <div className="rounded-[12px] border border-black/5 bg-white p-2">
                                    <img src={image} alt="Uploaded preview" className="mx-auto max-h-[420px] w-auto max-w-full rounded-[10px] object-contain" />
                                </div>
                            ) : (
                                <div className="rounded-[12px] border border-black/5 bg-white px-5 py-8 flex flex-col items-center justify-center">
                                    <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
                                        <PhotoIcon aria-hidden="true" className="h-8 w-8 text-primary" />
                                    </div>
                                    <p className="font-semibold text-[18px] pt-4">Choose a leaf photo</p>
                                    <p className="text-tertiary text-[15px] pt-1">The preview will keep the image shape.</p>
                                </div>
                            )}

                            <div className="mt-4 flex flex-col items-center gap-2">
                                <button
                                    type="button"
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        openFilePicker();
                                    }}
                                    className="rounded-[14px] bg-primary px-6 py-3 font-semibold text-white shadow-sm transition-opacity hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                                >
                                    <span>{image ? 'Change image' : 'Upload image'}</span>
                                </button>
                                <p className="text-[15px] text-tertiary">PNG, JPG, or GIF up to 5MB</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5">
                            <button onClick={handleImageUpload} disabled={loader || !selectedImage} className="py-[14px] text-[18px] text-white px-[24px] rounded-[14px] bg-quaternary disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:opacity-95 transition-opacity">
                                {loader ? 'Analyzing...' : 'Analyze image'}
                            </button>
                            <button onClick={handleViewReport} disabled={!reportPayload} className="py-[14px] text-[18px] text-white px-[24px] rounded-[14px] bg-primary disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:opacity-95 transition-opacity">
                                View results
                            </button>
                        </div>

                        <div className="mt-5 rounded-[14px] bg-[#F8FAF7] border border-black/5 p-4">
                            <p className="font-semibold text-[16px]">
                                {reportPayload ? 'Report ready' : selectedImage ? 'Ready to analyze' : 'Choose a clear leaf photo'}
                            </p>
                            <p className="text-[15px] text-tertiary pt-1">
                                {reportPayload
                                    ? 'Open the report page to review the result and treatment plan.'
                                    : selectedImage
                                        ? 'Run the model when the leaf is clearly visible in the preview.'
                                        : 'The guardrail accepts close-up tomato leaf images only.'}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-10 lg:mt-14 rounded-[20px] border border-black/5 bg-white p-5 lg:p-7 shadow-sm">
                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
                        <div>
                            <h2 className="text-[24px] lg:text-[30px] font-semibold">Diseases checked</h2>
                            <p className="text-[16px] text-tertiary pt-1">The backend evaluates whole-image and regional evidence.</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-5">
                        {[
                            ['Early Blight', 'Brown circular spots with concentric rings, usually on older leaves.'],
                            ['Late Blight', 'Dark, water-soaked lesions that spread quickly and collapse leaf tissue.'],
                            ['Leaf Mold', 'Yellow upper-leaf patches with mold growth in humid conditions.'],
                        ].map(([title, copy]) => (
                            <div key={title} className="rounded-[14px] border border-black/5 bg-[#FAFAF8] p-5">
                                <h3 className="font-semibold text-[18px]">{title}</h3>
                                <p className="text-tertiary text-[16px] pt-2 leading-relaxed">{copy}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Detect;
