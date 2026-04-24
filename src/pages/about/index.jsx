import aboutImg from '../../assets/photos/tomato-about.jpg'
import { Link } from 'react-router-dom';


const About = () => {
    return (<div className="px-[20px] lg:px-[120px]">
        <div className='flex flex-col-reverse lg:flex-row justify-between items-center gap-[40px] lg:gap-[56px] pt-[12px] lg:pt-[24px]'>
            <div className='lg:w-1/2'>
                <h1 className="text-[32px] lg:text-[42px] pb-[16px] hidden lg:block"><span className="font-bold">About</span> Us</h1>
                <p className='text-[18px] lg:text-[20px] leading-relaxed text-tertiary'>
                    Welcome to Tomato Planet, a tomato-focused disease detection and care assistant. We use modern image analysis to help you quickly recognize common tomato issues and choose practical next steps—so your plants stay productive from transplant to harvest.
                </p>
            </div>
            <div className='lg:w-1/2'>
                <img src={aboutImg} alt="Tomatoes on the vine" className="rounded-[18px] object-cover w-full max-h-[420px]" />
            </div>
            <h1 className="text-[32px] lg:text-[42px] lg:hidden"><span className="font-bold">About</span> Us</h1>

        </div>

        <div className='mt-12 lg:mt-16'>
            <h1 className="text-[30px] lg:text-[40px] pb-[16px]">Our <span className="font-bold">Mission
            </span></h1>
            <p className='text-[18px] lg:text-[20px] leading-relaxed text-tertiary'>
                We aim to empower growers with a simple workflow for tomato health checks: take a photo, get likely diagnoses, and receive prevention/treatment ideas that help reduce crop loss and improve yields.


            </p>
        </div>

        <div className='mt-10 lg:mt-14 rounded-[22px] border border-black/5 p-6 lg:p-10'>
            <h2 className='text-[26px] lg:text-[34px] font-semibold'>What we cover</h2>
            <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>We focus on signals you can see in real photos of your tomato plant.</p>
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-6'>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Leaf symptoms</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Spots, browning, yellowing, curling, and mildew-like patterns.</p>
                </div>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Fruit symptoms</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Discoloration, lesions, cracking, and surface damage.</p>
                </div>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Care context</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Simple prevention and treatment ideas to guide your next steps.</p>
                </div>
            </div>
        </div>

        <div className='mt-10 lg:mt-14'>
            <h1 className="text-[30px] lg:text-[40px] pb-[16px]">Why <span className="font-bold">Choose Us?
            </span></h1>
            <p className='text-[18px] lg:text-[20px] leading-relaxed text-tertiary'>
                Tomato Planet is built for clarity and speed. Upload a clear tomato leaf or fruit photo and we’ll summarize what it most likely is, why it happens, and how to respond.


            </p>
        </div>

        <div className='mt-10 lg:mt-14 grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 items-start'>
            <div className='rounded-[22px] border border-black/5 p-6 lg:p-10'>
                <h2 className='text-[26px] lg:text-[34px] font-semibold'>How results are presented</h2>
                <ul className='pt-4 space-y-3 text-[16px] lg:text-[18px] text-tertiary leading-relaxed list-disc pl-5'>
                    <li>Top likely matches (with probabilities)</li>
                    <li>Short description + “learn more” reference links</li>
                    <li>Prevention, biological, and chemical treatment ideas (when available)</li>
                </ul>
            </div>
            <div className='rounded-[22px] bg-quaternary text-white p-6 lg:p-10'>
                <h2 className='text-[26px] lg:text-[34px] font-semibold'>Privacy &amp; trust</h2>
                <p className='pt-3 text-white/80 text-[16px] lg:text-[18px] leading-relaxed'>Your upload is used to generate results. If you want, we can add a dedicated privacy page that clearly states retention and deletion behavior.</p>
                <div className='pt-6'>
                    <Link to={'/contact'} className='inline-block py-[12px] text-[16px] text-quaternary px-[22px] rounded-[14px] bg-white shadow-sm hover:opacity-95 transition-opacity'>Ask a question</Link>
                </div>
            </div>
        </div>

        <div className='mt-10 lg:mt-14'>
            <h1 className="text-[30px] lg:text-[40px] pb-[16px] text-center"><span className="font-bold">Explore
            </span> More</h1>
            <p className='text-[18px] lg:text-[20px] lg:px-[20%] text-center text-tertiary leading-relaxed'>
                Ready to check your tomatoes? Head to <Link to={'/detect'} className='underline text-primary hover:text-secondary'>Analyze</Link> and upload a photo.
            </p>
        </div>
    </div>);
}

export default About;