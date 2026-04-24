import ellipse from '../../assets/ellipse.svg'
import { useState } from 'react'


const Contact = () => {
  const [first, setFirst] = useState('')
  const [email, setEmail] = useState('')
  const [category, setCategory] = useState('')
  const [message, setMessage] = useState('')
  const [number, setNumber] = useState('')

  return (
    <>
      <div className="px-[20px] lg:px-[120px] flex justify-between items-center flex-col lg:flex-row pt-[12px] lg:pt-[24px]">
        <div className='p-[10px] flex-col lg:flex-row w-full flex justify-between items-center lg:items-start gap-[0px]'>
          <div className="w-[100%] lg:w-[50%] bg-primary relative rounded-[10px] p-[15px] lg:p-[40px] flex flex-col justify-between items-center lg:items-start gap-[60px] lg:gap-[140px]">
            <div className="flex flex-col items-center lg:items-start gap-[6px]">
              <h1 className="text-[20px] lg:text-[28px] text-white text-center lg:text-left">
                Contact Information
              </h1>
              <p className="text-[#C9C9C9]  text-[11px] lg:text-[18px] text-center lg:text-left">
                Questions about tomato photos or results? Send us a message.
              </p>
            </div>
            <div className="flex flex-col items-center lg:items-start justify-between gap-[15px] lg:gap-[50px]">
              <div className="flex flex-col lg:flex-row justify-center lg:justify-start items-center gap-[10px] lg:gap-[25px]">
                {/* <img src={contactPhone} alt="" /> */}
                <p className=" lg:text-[16px] text-center lg:text-left  text-white">
                  +234 700800IITA (4482), +1 201 6336094
                </p>
              </div>
              <div className="flex flex-col lg:flex-row justify-center lg:justify-start  items-center gap-[10px] lg:gap-[25px]">
                {/* <img src={contactMail} alt="" /> */}
                <p className=" lg:text-[16px] text-center lg:text-left  text-white">
                  IITA-Ckan@cgiar.org
                </p>
              </div>
              <div className="flex flex-col lg:flex-row relative z-[999] justify-center lg:justify-start  items-center gap-[10px] lg:gap-[25px]">
                {/* <img src={contactLocation} alt="" /> */}
                <p className=" lg:text-[16px] text-center lg:text-left  text-white">
                  PMB 5320, Oyo Road, Ibadan 200001,
                  Oyo State, Nigeria.
                </p>
              </div>
            </div>
            <div className="flex justify-start items-center gap-[24px] z-20">
              {/* <a
                href="https://www.facebook.com/profile.php?id=100064006633921&mibextid=2JQ9oc"
                target="_blank"
                rel="noreferrer"
              >
              </a> */}
              {/* <img src={contactInsta} alt="" /> */}
              {/* <img src={contactX} alt="" /> */}
            </div>
            <div className="absolute bottom-0 right-0 z-0 w-[30%] lg:w-[45%]">
              <img src={ellipse} alt="" className="w-full rounded-b-[10px]" />
            </div>
          </div>


          <div className='w-[100%] lg:w-[50%] flex flex-col justify-start items-start px-[20px] py-[30px] lg:p-[50px] gap-[45px]  h-full'>
            <div className='w-full rounded-[18px] border border-black/10 p-4 lg:p-5 text-tertiary'>
              <p className='text-[14px] lg:text-[16px]'><span className='font-semibold text-black'>Typical response time:</span> 1–2 business days.</p>
              <p className='text-[14px] lg:text-[16px] pt-2'>For faster help, include a screenshot of your result and mention your tomato variety + growing setup (garden/greenhouse/pots).</p>
            </div>
            <div className='flex flex-col lg:flex-row justify-between items-center gap-[40px] w-full'>
              <div className='flex justify-start flex-col w-[100%] lg:w-[50%] group'>
                <label htmlFor="fName" className=''>Full Name</label>
                <input type="text" placeholder='Enter full name...' id='fName' className='outline-none border-b-[1px] h-[50px] border-b-black p-2  text-[14px] text-black' value={first} onChange={(e) => setFirst(e.target.value)} />
              </div>
              <div className='flex justify-start flex-col w-[100%] lg:w-[50%] group'>
                <label htmlFor="lName" className=' item'>Subject</label>
                <input type="text" placeholder='Enter subject...' id='lName' className='outline-none border-b-[1px] h-[50px] border-b-black p-2  text-[14px] text-black' value={category} onChange={(e) => setCategory(e.target.value)} />
              </div>
            </div>
            <div className='flex flex-col lg:flex-row justify-between items-center gap-[40px] w-full'>
              <div className='flex justify-start flex-col w-[100%] lg:w-[50%] group'>
                <label htmlFor="mail" className=''>Email</label>
                <input type="email" placeholder='Enter email address...' id='mail' className='outline-none border-b-[1px] h-[50px] border-b-black p-2  text-[14px] text-black' value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <div className='flex justify-start flex-col w-[100%] lg:w-[50%] group'>
                <label htmlFor="lName" className=''>Phone Number</label>
                <input type="text" placeholder='Enter phone number...' id='lName' className='outline-none border-b-[1px] h-[50px] border-b-black p-2  text-[14px] text-black' value={number} onChange={(e) => setNumber(e.target.value)} />
              </div>
            </div>
            <div className='flex justify-start flex-col w-[100%] group'>
              <label htmlFor="mail" className=''>Message</label>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder='Write your message...' id='mail' className='outline-none border-b-[1px] h-[200px] border-b-black p-2  text-[14px] text-black' />
            </div>
            <div className='flex w-full items-end justify-center lg:justify-end'>
              <a href={`mailto:IITA-Ckan@cgiar.org?subject=${category}&body=Name: ${first} %0D%0A Email: ${email}%0D%0A Phone: ${number}%0D%0A Message: ${message}`} className='bg-primary w-full lg:w-[40%] text-white px-[24px] font-[500] text-center rounded-[8px] border-secondary border-[2px] py-[8px] send'>Send Message
              </a>
            </div>

            <div className='w-full pt-4'>
              <h2 className='text-[22px] lg:text-[28px] font-semibold'>FAQ</h2>
              <div className='pt-4 space-y-4'>
                <div className='rounded-[18px] border border-black/10 p-4 lg:p-5'>
                  <h3 className='font-semibold'>What should I include in my message?</h3>
                  <p className='text-tertiary pt-2 text-[14px] lg:text-[16px] leading-relaxed'>Tell us what you uploaded (leaf/fruit), what you expected, and attach a screenshot of the result if possible.</p>
                </div>
                <div className='rounded-[18px] border border-black/10 p-4 lg:p-5'>
                  <h3 className='font-semibold'>Can you help with non-tomato plants?</h3>
                  <p className='text-tertiary pt-2 text-[14px] lg:text-[16px] leading-relaxed'>This site is tuned for tomatoes. For best results, upload only tomato leaves, stems, or fruit.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </>
  );
}

export default Contact;