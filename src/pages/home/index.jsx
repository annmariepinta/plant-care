import img1 from '../../assets/photos/tomato-hero-1.jpg'
import img2 from '../../assets/photos/tomato-hero-2.jpg'
import img3 from '../../assets/photos/tomato-hero-3.jpg'
import img4 from '../../assets/photos/tomato-hero-4.jpg'
import ellipse1 from '../../assets/curveBottom.svg'
import ellipse2 from '../../assets/curveTop.svg'
import slide1 from '../../assets/photos/tomato-slide-1.jpg'
import slide2 from '../../assets/photos/tomato-slide-2.jpg'
import slide3 from '../../assets/photos/tomato-slide-3.jpg'
import slide4 from '../../assets/photos/tomato-slide-4.jpg'
import slide5 from '../../assets/photos/tomato-slide-5.jpg'
import slide6 from '../../assets/photos/tomato-slide-6.jpg'
import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'


const Home = () => {
    const slides = useMemo(() => ([
        { src: slide1, alt: 'Tomato leaves and fruit' },
        { src: slide2, alt: 'Tomatoes growing in a greenhouse' },
        { src: slide3, alt: 'Tomatoes growing on a plant' },
        { src: slide4, alt: 'Tomato plant leaves close-up' },
        { src: slide5, alt: 'Bunch of tomatoes on a vine' },
        { src: slide6, alt: 'Ripe tomatoes on the vine' },
    ]), []);

    const [activeSlide, setActiveSlide] = useState(0);
    useEffect(() => {
        const id = window.setInterval(() => {
            setActiveSlide((i) => (i + 1) % slides.length);
        }, 4500);
        return () => window.clearInterval(id);
    }, [slides.length]);

    return (<div className="px-[20px] lg:px-[120px]">
        <div className="flex flex-col-reverse lg:flex-row justify-between items-center gap-[40px] lg:gap-[56px] pt-[12px] lg:pt-[24px]">
            <div className="lg:w-1/2">
                <h1 className="lg:text-[42px] text-[32px] leading-tight text-center lg:text-left">Welcome to <span className="font-bold">Tomato Planet</span></h1>

                <p className='text-[18px] lg:pl-1 lg:text-[22px] leading-relaxed text-tertiary pt-3 pb-[24px] text-center lg:text-left'>At Tomato Planet, we focus on what matters most for growers: healthy tomato plants and reliable harvests. Upload a clear photo of your tomato leaf (or fruit) to quickly spot issues and get practical treatment guidance.</p>

                <div className='flex justify-center items-center lg:justify-start'>
                    <Link to={'/detect'} className='py-[12px] text-[16px] text-white px-[28px] rounded-[14px] bg-primary shadow-sm hover:opacity-95 transition-opacity'>Begin Analysis</Link>
                </div>
            </div>
            <div className="lg:w-1/2 flex gap-[20px]">
                <div className='flex flex-col gap-[20px]'>
                    <img src={img1} alt="Tomato plant" className="rounded-[16px] object-cover w-full h-[190px] lg:h-[220px]" />
                    <img src={img2} alt="Tomatoes on vine" className="rounded-[16px] object-cover w-full h-[190px] lg:h-[220px]" />
                </div>
                <div className='flex flex-col gap-[20px]'>
                    <img src={img3} alt="Tomato harvest" className="rounded-[16px] object-cover w-full h-[190px] lg:h-[220px]" />
                    <img src={img4} alt="Tomato leaves" className="rounded-[16px] object-cover w-full h-[190px] lg:h-[220px]" />
                </div>
            </div>
        </div>

        <div className='flex justify-center items-center mt-[56px] lg:mt-[72px] pb-[28px] lg:pb-[36px]'>
            <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6'>
            <div className='rounded-[18px] border border-black/5 p-5 lg:p-6'>
                <p className='text-[14px] text-tertiary'>Step 1</p>
                <h3 className='text-[18px] lg:text-[20px] font-semibold pt-2'>Upload a clear photo</h3>
                <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>Use a close-up of the tomato leaf (front and back) or fruit. Natural light helps.</p>
            </div>
            <div className='rounded-[18px] border border-black/5 p-5 lg:p-6'>
                <p className='text-[14px] text-tertiary'>Step 2</p>
                <h3 className='text-[18px] lg:text-[20px] font-semibold pt-2'>Get likely matches</h3>
                <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>We return probable issues and a quick health summary you can act on.</p>
            </div>
            <div className='rounded-[18px] border border-black/5 p-5 lg:p-6'>
                <p className='text-[14px] text-tertiary'>Step 3</p>
                <h3 className='text-[18px] lg:text-[20px] font-semibold pt-2'>Follow treatment tips</h3>
                <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>See prevention, biological, and chemical options (where applicable).</p>
            </div>
        </div>

        <div className='flex justify-center items-center mt-[56px] lg:mt-[72px] pb-[28px] lg:pb-[36px]'>
            <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
        </div>

        <div className=''>
            <h1 className="text-[30px] lg:text-[40px] text-center pb-[16px]">Why <span className="font-bold">Choose Us?
            </span></h1>
            <p className='text-[18px] lg:text-[20px] leading-relaxed text-tertiary'>
                Tomato Planet is designed to be fast and practical. Whether you grow tomatoes in a backyard bed, a greenhouse, or a farm plot, our tools help you recognize common tomato issues early and respond with confidence.
            </p>
            <ul className='text-[18px] lg:text-[20px] text-tertiary list-disc pl-4 lg:pl-0 px-4 mt-4 space-y-2'>
                <li>Tomato Disease Detection: Identify common tomato problems from a single photo.
                </li>
                <li>Actionable Next Steps: Clear treatment and prevention ideas you can apply right away.
                </li>
                <li>Grower-Friendly Tips: Watering, pruning, and nutrition reminders tuned for tomatoes.
                </li>
            </ul>
        </div>

        <div className='flex justify-center items-center mt-[56px] lg:mt-[72px] pb-[28px] lg:pb-[36px]'>
            <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
        </div>

        <div className='rounded-[22px] border border-black/5 bg-white p-6 lg:p-10'>
            <div className='flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6'>
                <div>
                    <h2 className='text-[26px] lg:text-[34px] font-semibold'>Common tomato issues we help you spot</h2>
                    <p className='text-[16px] lg:text-[18px] text-tertiary pt-2 leading-relaxed'>Examples include leaf spots, blights, mold, nutrient stress, and pest damage.</p>
                </div>
                <Link to={'/detect'} className='py-[12px] text-[16px] text-white px-[22px] rounded-[14px] bg-primary shadow-sm hover:opacity-95 transition-opacity whitespace-nowrap'>Analyze a photo</Link>
            </div>
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-5 pt-6'>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Leaf spots</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Small circular lesions, halos, or speckling—often worsens after wet weather.</p>
                </div>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Blight patterns</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Fast spreading browning, leaf collapse, or dark lesions that move upward.</p>
                </div>
                <div className='rounded-[18px] border border-black/5 p-5'>
                    <h3 className='font-semibold text-[18px]'>Pest damage</h3>
                    <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Chew marks, mines, curling leaves, or stunted new growth.</p>
                </div>
            </div>
            <p className='text-[14px] text-tertiary pt-4'>Note: results are informational and depend on photo quality.</p>
        </div>

        <div className='flex justify-center items-center mt-[56px] lg:mt-[72px] pb-[28px] lg:pb-[36px]'>
            <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
        </div>

        <div className='flex flex-col items-center'>
            <h2 className='text-[30px] lg:text-[40px]'><span className='font-bold'>Tomato</span> highlights</h2>
            <p className='text-[18px] text-center lg:text-left lg:text-[20px] text-tertiary pt-[12px] pb-[24px]'>Quick checks for common tomato leaf &amp; fruit issues</p>

            <div className='relative w-full'>
                <img src={ellipse1} className='pointer-events-none absolute z-0 hidden lg:block -top-12 w-full opacity-60' alt="" />
                <img src={ellipse2} className='pointer-events-none absolute z-0 hidden lg:block -bottom-10 w-full opacity-60' alt="" />

                <div className="relative z-10 overflow-hidden">
                    <div
                        className="flex transition-transform duration-500 ease-out gap-6 lg:gap-8"
                        style={{
                            transform: `translateX(calc(${activeSlide} * -240px))`,
                        }}
                    >
                        {slides.concat(slides.slice(0, 3)).map((s, idx) => (
                            <img
                                key={`${s.src}-${idx}`}
                                src={s.src}
                                alt={s.alt}
                                className="rounded-[18px] object-cover w-[220px] h-[260px] shadow-sm flex-none bg-white"
                                draggable={false}
                            />
                        ))}
                    </div>
                </div>

                <div className="relative z-10 flex justify-center items-center gap-3 pt-6">
                    <button
                        type="button"
                        onClick={() => setActiveSlide((i) => (i - 1 + slides.length) % slides.length)}
                        className="px-4 py-2 rounded-[12px] border border-black/10 text-[14px] hover:bg-black/5 transition-colors"
                    >
                        Prev
                    </button>
                    <div className="flex items-center gap-2">
                        {slides.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                onClick={() => setActiveSlide(i)}
                                className={`h-[10px] w-[10px] rounded-full transition-colors ${i === activeSlide ? 'bg-primary' : 'bg-black/15'}`}
                                aria-label={`Go to slide ${i + 1}`}
                            />
                        ))}
                    </div>
                    <button
                        type="button"
                        onClick={() => setActiveSlide((i) => (i + 1) % slides.length)}
                        className="px-4 py-2 rounded-[12px] border border-black/10 text-[14px] hover:bg-black/5 transition-colors"
                    >
                        Next
                    </button>
                </div>
            </div>
        </div>

        <div className='flex justify-center items-center mt-[56px] lg:mt-[72px] pb-[28px] lg:pb-[36px]'>
            <div className='h-[4px] rounded-[10px] w-[70%] bg-quaternary'></div>
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 items-start'>
            <div>
                <h2 className='text-[26px] lg:text-[34px] font-semibold'>FAQ</h2>
                <div className='pt-4 space-y-4'>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>What photo works best?</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Use natural light, focus on the affected area, and include one close-up plus one wider shot of the plant.</p>
                    </div>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>Can I upload tomato fruit images too?</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>Yes—fruit issues like discoloration, lesions, or cracking can also be assessed.</p>
                    </div>
                    <div className='rounded-[18px] border border-black/5 p-5'>
                        <h3 className='font-semibold text-[18px]'>Do you store my images?</h3>
                        <p className='text-tertiary text-[16px] pt-2 leading-relaxed'>We only use your upload to generate results. If you want a stricter policy, we can add an explicit “no storage” note on the site.</p>
                    </div>
                </div>
            </div>
            <div className='rounded-[22px] bg-quaternary text-white p-6 lg:p-10'>
                <h3 className='text-[22px] lg:text-[28px] font-semibold'>Ready to check your tomato plant?</h3>
                <p className='text-[16px] lg:text-[18px] pt-3 text-white/80 leading-relaxed'>Upload a photo and get likely matches plus treatment guidance in minutes.</p>
                <div className='pt-6'>
                    <Link to={'/detect'} className='inline-block py-[12px] text-[16px] text-quaternary px-[22px] rounded-[14px] bg-white shadow-sm hover:opacity-95 transition-opacity'>Go to Analyze</Link>
                </div>
            </div>
        </div>
    </div>);
}

export default Home;