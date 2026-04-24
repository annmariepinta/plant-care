// import ImageUploader from "../../components/ImageUploader";
import { useState, useRef } from 'react';
import axios from 'axios';
import { useAppToast } from '../../lib/UseAppToast';
import { PhotoIcon } from '@heroicons/react/16/solid'
// import CustomModal from './Modal';
import ReactToPrint from "react-to-print";

const Detect = () => {
    const componentRef = useRef();
    const toast = useAppToast();
    const [selectedImage, setSelectedImage] = useState(null);
    const [image, setImage] = useState(null);
    const [show, setShow] = useState(false);
    const [result, setResult] = useState([]);
    const [imageResult, setImageResult] = useState('');

    const handleShow = () => {
        setShow(true);
    };

    // const handleClose = () => {
    //     setShow(!show);
    // };

    const [loader, setLoader] = useState(false);

    const handleImageUpload = async () => {
        if (!image) {
            toast({
                status: "error",
                description: "Please select an image",
            });
            return;
        }
        setResult([])
        const formData = new FormData();
        formData.append('file', selectedImage);
        setLoader(true);
        try {
            const response = await axios.post(
                'https://plant.id/api/v3/health_assessment?details=local_name,description,url,treatment,classification,common_names,cause',
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                        'Api-Key': import.meta.env.VITE_API_BASE_URL,
                    },
                }
            );
            toast({
                status: "success",
                description: response.message || "Assessment Successful",
            });
            // Handle the response from the API
            console.log(response.data);
            setImageResult(response.data.input.images[0])
            if (response?.data?.result?.is_plant?.binary === true) {
                setResult(response.data.result)
                handleShow()
            } else {
                toast({
                    status: "error",
                    description: "This doesn't look like a plant. Please upload a clearer tomato plant/leaf image.",
                });
            }
            setLoader(false);
        } catch (error) {
            console.error(error);
            setLoader(false);
        }
    };

    const handleImageChange = (event) => {
        setSelectedImage(event.target.files[0]);
        const file = event.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
                setImage(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };


    return (
        <div className="px-[20px] lg:px-[120px] overflow-x-hidden">
            <div className='flex flex-col lg:flex-row justify-between items-center gap-[56px]'>
                <div className='lg:w-1/2'>
                    <h1 className="text-[36px] lg:text-[48px] pb-[20px]">How To <span className="font-bold">Detect</span></h1>

                    <ul className='text-[18px] lg:text-[24px] list-disc pl-4 lg:pl-0 px-4 text-tertiary'>
                        <li>Click on the &quot;Upload a file&quot; button. Select a clear photo of the affected tomato leaf (or fruit) for the most accurate analysis.
                        </li>
                        <li>After uploading, click the &quot;Analyze&quot; button to initiate the disease detection process.
                        </li>
                        <li>Once the analysis is complete, you will receive a detailed report containing:
                        </li>
                        <p className='pl-3'>- Three possible diseases that match the symptoms observed in the image. <br />
                            - The health status of the plant. <br />
                            - The names of the diseases. <br />
                            - A brief description of each disease. <br />
                            - Suggested treatments to manage the detected diseases effectively.</p>
                    </ul>

                    <div className='mt-8 rounded-[22px] border border-black/5 p-5 lg:p-6'>
                        <h2 className='text-[20px] lg:text-[22px] font-semibold'>Photo tips for better results</h2>
                        <ul className='mt-3 space-y-2 text-[16px] lg:text-[18px] text-tertiary list-disc pl-5 leading-relaxed'>
                            <li>Use bright natural light (avoid harsh shadows)</li>
                            <li>Take one close-up of the affected area + one wider plant shot</li>
                            <li>For leaves: capture both the front and underside</li>
                            <li>Avoid blurry photos and busy backgrounds</li>
                        </ul>
                    </div>
                </div>
                <div className='lg:w-1/2 flex justify-center items-center w-full'>
                    <div className='flex flex-col justify-center w-full items-center gap-10 overflow-x-hidden text-tertiary'>
                        {/* <input type="file" accept="image/*" onChange={handleImageChange} /> */}
                        <div className="text-center border-primary border-[2px] border-dashed p-8 lg:p-16 rounded-[8px]">
                            {image ? (
                                <img src={image} alt="Uploaded preview" className="mx-auto h-20 w-26 object-cover rounded-md" />
                            ) : (
                                <PhotoIcon aria-hidden="true" className="mx-auto h-20 w-20 text-gray-300" />
                            )}
                            <div className="mt-4 mb-2 flex text-[16px] leading-6">
                                <label
                                    className="relative cursor-pointer rounded-md font-semibold text-primary focus-within:outline-none focus-within:ring-2 focus-within:ring-primary focus-within:ring-offset-2 hover:text-secondary outline-none border-none"
                                >
                                    <span className="px-1 whitespace-nowrap">Upload a file</span>
                                    <input
                                        type="file" accept="image/*" onChange={handleImageChange} className="sr-only"
                                    />
                                </label>
                                <p className="pl-2 whitespace-nowrap">or drag and drop</p>
                            </div>
                            <p className="text-[16px] leading-5">PNG, JPG, GIF up to 5MB</p>
                        </div>
                        <button onClick={handleImageUpload} className='py-[15px] text-[20px] text-white px-[55px] rounded-[20px] bg-primary'>{loader ? (
                            <svg
                                className="animate-spin h-5 w-5 mr-3 text-white"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                ></circle>
                                <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8v8H4z"
                                ></path>
                            </svg>
                        ) : (
                            <>
                                Analyze
                            </>
                        )}
                        </button>
                    </div>
                </div>
            </div>

            <div className='mt-12 lg:mt-16 rounded-[22px] border border-black/5 bg-white p-6 lg:p-10'>
                <h2 className='text-[26px] lg:text-[34px] font-semibold'>What you can check</h2>
                <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>Upload tomato plant photos to help spot common leaf and fruit symptoms.</p>
                <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-5 pt-6'>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>Leaf spots &amp; blotches</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Speckling, rings, or spreading lesions.</p>
                    </div>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>Blight-like browning</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Rapid browning, leaf collapse, or darkening.</p>
                    </div>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>Pest &amp; stress signals</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Chewing, curling, yellowing, or stunted growth.</p>
                    </div>
                </div>
            </div>

            <div className='pt-[100px] '>
                {show && (
                    <div ref={componentRef}>
                        <h1 className='text-center text-[34px]'>Assessment Result</h1>

                        <div className='flex justify-center items-center py-10'>
                            <img src={imageResult} alt="" className='lg:w-[50%] w-[70%]' />
                        </div>

                        <div className='flex flex-col w-full gap-3 items-start'>
                            {result.length > 0 && <p className='font-bold text-[22px]'>Health Status: <span className={`${result?.is_healthy?.binary ? "text-green-500" : 'text-red-500'}`}>{result && result?.is_healthy?.binary ? "Healthy" : "Not healthy"}</span></p>}

                            <div>
                                <p className='font-semibold text-[22px] pb-3'>Possible Disease(s):</p>
                                <div className='flex flex-col w-full items-start gap-16'>
                                    {result && result?.disease && result?.disease?.suggestions.slice(0, 3).map((disease, i) => {
                                        return (
                                            <div key={i} className='flex flex-col items-start gap-4'>
                                                <h1 className='font-semibold text-[20px]'>{i + 1}. Name: {disease.name}</h1>
                                                <h1 className='font-semibold text-[20px]'>Probability: {disease.probability * 100}%</h1>

                                                <div className='text-tertiary'>
                                                    <p className='text-[18px]'><span className='font-semibold text-[20px] text-black'>Description:</span> {disease?.details.description}</p>
                                                    <a href={disease?.details.url} target="_blank" rel="noopener noreferrer" className='text-primary underline font-semibold mt-1'>Learn More</a>
                                                </div>

                                                <div>
                                                    <p className='font-semibold pb-2 text-[20px]'>Treatment</p>
                                                    <div className='flex flex-col w-full gap-3'>

                                                        <div>
                                                            <h1 className='text-[18px] font-semibold'>Biological Treatment</h1>
                                                            {disease?.details?.treatment?.biological && disease?.details?.treatment?.biological.map((biological, i) => {
                                                                return (
                                                                    <div key={i} className='text-tertiary'>
                                                                        <div>
                                                                            <ul className='list-disc pl-4 lg:pl-0'>
                                                                                <li key={i} className='text-[18px]'>{biological}</li>
                                                                            </ul>
                                                                        </div>
                                                                    </div>
                                                                )
                                                            })}
                                                        </div>
                                                        <div>
                                                            <h1 className='text-[18px] font-semibold'>Chemical Treatment</h1>
                                                            {disease?.details?.treatment?.chemical && disease?.details?.treatment?.chemical.map((chemical, i) => {
                                                                return (
                                                                    <div key={i} className='text-tertiary'>
                                                                        <div>
                                                                            <ul className='list-disc pl-4 lg:pl-0'>
                                                                                <li key={i} className='text-[18px]'>{chemical}</li>
                                                                            </ul>
                                                                        </div>
                                                                    </div>
                                                                )
                                                            })}
                                                        </div>
                                                        <div>
                                                            <h1 className='text-[18px] font-semibold'>Prevention</h1>
                                                            {disease?.details?.treatment?.prevention && disease?.details?.treatment?.prevention.map((prevention, i) => {
                                                                return (
                                                                    <div key={i} className='text-tertiary'>
                                                                        <div>
                                                                            <ul className='list-disc pl-4 lg:pl-0'>
                                                                                <li key={i} className='text-[18px]'>{prevention}</li>
                                                                            </ul>
                                                                        </div>
                                                                    </div>
                                                                )
                                                            })}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        </div>
                        <ReactToPrint
                            trigger={() => <button className='py-[15px] text-[20px] text-white px-[55px] rounded-[20px] bg-primary mt-5'>Print this section</button>}
                            content={() => componentRef.current}
                        />
                    </div>
                )}
            </div>

            <div className='flex justify-center items-center mt-[80px] pb-[40px]'>
                <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
            </div>
        </div>);
}

export default Detect;